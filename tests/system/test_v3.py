"""Define tests for v3 System objects."""
# pylint: disable=unused-argument
from datetime import datetime
import logging

import aiohttp
import pytest
import pytz

from simplipy import get_api
from simplipy.errors import (
    EndpointUnavailableError,
    InvalidCredentialsError,
    PinError,
    RequestError,
    SimplipyError,
)
from simplipy.system import SystemStates
from simplipy.system.v3 import VOLUME_HIGH, VOLUME_MEDIUM

from tests.common import (
    TEST_CLIENT_ID,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    TEST_USER_ID,
    load_fixture,
)


@pytest.mark.parametrize(
    "v3_subscriptions_response",
    ["subscriptions_alarm_state_response"],
    indirect=True,
)
async def test_alarm_state(v3_server):
    """Test handling of a triggered alarm."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert system.state == SystemStates.alarm


async def test_clear_notifications(v3_server):
    """Test getting the latest event."""
    v3_server.delete(
        f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/messages",
        status=200,
        body=load_fixture("v3_settings_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        await system.clear_notifications()
        assert system.notifications == []


async def test_get_last_event(v3_server):
    """Test getting the latest event."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/events?numEvents=1"
        ),
        status=200,
        body=load_fixture("latest_event_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        latest_event = await system.get_latest_event()
        assert latest_event["eventId"] == 1234567890


async def test_get_pins(v3_server, v3_settings_response):
    """Test getting PINs associated with a V3 system."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=200,
        body=v3_settings_response,
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        pins = await system.get_pins()
        assert len(pins) == 4
        assert pins["master"] == "1234"
        assert pins["duress"] == "9876"
        assert pins["Test 1"] == "3456"
        assert pins["Test 2"] == "5423"


async def test_get_systems(v3_server, v3_subscriptions_response, v3_settings_response):
    """Test the ability to get systems attached to a v3 account."""
    v3_server.post(
        "https://api.simplisafe.com/v1/api/token",
        status=200,
        body=load_fixture("api_token_response.json"),
    )
    v3_server.get(
        "https://api.simplisafe.com/v1/api/authCheck",
        status=200,
        body=load_fixture("auth_check_response.json"),
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/users/{TEST_USER_ID}"
            "/subscriptions?activeOnly=true"
        ),
        status=200,
        body=v3_subscriptions_response,
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=200,
        body=v3_settings_response,
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/sensors?forceUpdate=false"
        ),
        status=200,
        body=load_fixture("v3_sensors_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        assert len(systems) == 1

        system = systems[TEST_SYSTEM_ID]

        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.system_id == TEST_SYSTEM_ID
        assert len(system.sensors) == 24


async def test_empty_events(v3_server):
    """Test that an empty events structure is handled correctly."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/events?numEvents=1"
        ),
        status=200,
        body=load_fixture("events_empty_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        # Test the events key existing, but being empty:
        with pytest.raises(SimplipyError):
            _ = await system.get_latest_event()


async def test_lock_state_update_bug(caplog, v3_server):
    """Test halting updates within a 15-second window from arming/disarming."""
    caplog.set_level(logging.INFO)

    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state/away"
        ),
        status=200,
        body=load_fixture("v3_state_away_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        await system.set_away()
        assert system.state == SystemStates.away
        await system.update()
        assert any("Skipping system update" in e.message for e in caplog.records)


async def test_missing_events(v3_server):
    """Test that an altogether-missing events structure is handled correctly."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/events?numEvents=1"
        ),
        status=200,
        body=load_fixture("events_missing_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        # Test the events key existing, but being empty:
        with pytest.raises(SimplipyError):
            _ = await system.get_latest_event()


@pytest.mark.parametrize(
    "subscriptions_fixture_filename",
    ["subscriptions_missing_system_response.json"],
)
async def test_missing_system_info_initial(caplog, v3_server):
    """Test that missing system data on system load is handled correctly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        assert systems == {}
        assert any(
            "Skipping location with missing system data" in e.message
            for e in caplog.records
        )


@pytest.mark.parametrize(
    "v3_subscriptions_response",
    ["subscriptions_offline_missing_response"],
    indirect=True,
)
async def test_missing_property(caplog, v3_server, v3_subscriptions_response):
    """Test that the missing property guard works properly."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/users/{TEST_USER_ID}"
            "/subscriptions?activeOnly=true"
        ),
        status=200,
        body=v3_subscriptions_response,
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        await system.update(include_settings=False, include_entities=False)

        assert system.offline is True
        assert any(
            "SimpliSafe didn't return data for property: offline" in e.message
            for e in caplog.records
        )


async def test_no_state_change_on_failure(v3_server):
    """Test that the system doesn't change state on an error."""
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state/away"
        ),
        status=401,
        body="Unauthorized",
    )
    v3_server.post(
        "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
    )
    v3_server.post(
        "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        assert system.state == SystemStates.off

        with pytest.raises(InvalidCredentialsError):
            await system.set_away()
        assert system.state == SystemStates.off


async def test_properties(v3_server, v3_settings_response):
    """Test that v3 system properties are available."""
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal"
        ),
        status=200,
        body=v3_settings_response,
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        assert system.alarm_duration == 240
        assert system.alarm_volume == VOLUME_HIGH
        assert system.battery_backup_power_level == 5293
        assert system.chime_volume == VOLUME_MEDIUM
        assert system.connection_type == "wifi"
        assert system.entry_delay_away == 30
        assert system.entry_delay_home == 30
        assert system.exit_delay_away == 60
        assert system.exit_delay_home == 0
        assert system.gsm_strength == -73
        assert system.light is True
        assert system.offline is False
        assert system.power_outage is False
        assert system.rf_jamming is False
        assert system.voice_prompt_volume == VOLUME_MEDIUM
        assert system.wall_power_level == 5933
        assert system.wifi_ssid == "MY_WIFI"
        assert system.wifi_strength == -49

        # Test "setting" various system properties by overriding their values, then
        # calling the update functions:
        system.settings_data["settings"]["normal"]["alarmDuration"] = 0
        system.settings_data["settings"]["normal"]["alarmVolume"] = 0
        system.settings_data["settings"]["normal"]["doorChime"] = 0
        system.settings_data["settings"]["normal"]["entryDelayAway"] = 0
        system.settings_data["settings"]["normal"]["entryDelayHome"] = 0
        system.settings_data["settings"]["normal"]["exitDelayAway"] = 0
        system.settings_data["settings"]["normal"]["exitDelayHome"] = 1000
        system.settings_data["settings"]["normal"]["light"] = False
        system.settings_data["settings"]["normal"]["voicePrompts"] = 0

        await system.set_properties(
            {
                "alarm_duration": 240,
                "alarm_volume": VOLUME_HIGH,
                "chime_volume": VOLUME_MEDIUM,
                "entry_delay_away": 30,
                "entry_delay_home": 30,
                "exit_delay_away": 60,
                "exit_delay_home": 0,
                "light": True,
                "voice_prompt_volume": VOLUME_MEDIUM,
            }
        )
        assert system.alarm_duration == 240
        assert system.alarm_volume == VOLUME_HIGH
        assert system.chime_volume == VOLUME_MEDIUM
        assert system.entry_delay_away == 30
        assert system.entry_delay_home == 30
        assert system.exit_delay_away == 60
        assert system.exit_delay_home == 0
        assert system.light is True
        assert system.voice_prompt_volume == VOLUME_MEDIUM


async def test_remove_nonexistent_pin(v3_server, v3_settings_response):
    """Test throwing an error when removing a nonexistent PIN."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=true"
        ),
        status=200,
        body=v3_settings_response,
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(PinError) as err:
            await system.remove_pin("0000")
            assert "Refusing to delete nonexistent PIN" in str(err)


async def test_remove_pin(v3_server, v3_settings_response):
    """Test removing a PIN in a V3 system."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=200,
        body=v3_settings_response,
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=true"
        ),
        status=200,
        body=v3_settings_response,
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/pins"
        ),
        status=200,
        body=load_fixture("v3_settings_deleted_pin_response.json"),
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=200,
        body=load_fixture("v3_settings_deleted_pin_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        latest_pins = await system.get_pins()
        assert len(latest_pins) == 4

        await system.remove_pin("Test 2")
        latest_pins = await system.get_pins()
        assert len(latest_pins) == 3


async def test_remove_reserved_pin(v3_server, v3_settings_response):
    """Test throwing an error when removing a reserved PIN."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=true"
        ),
        status=200,
        body=v3_settings_response,
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(PinError) as err:
            await system.remove_pin("master")
            assert "Refusing to delete reserved PIN" in str(err)


async def test_set_duplicate_pin(v3_server, v3_settings_response):
    """Test throwing an error when setting a duplicate PIN."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=true"
        ),
        status=200,
        body=v3_settings_response,
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/pins"
        ),
        status=200,
        body=v3_settings_response,
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await get_api(
                TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
            )

            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.set_pin("whatever", "1234")
            assert "Refusing to create duplicate PIN" in str(err)


async def test_set_invalid_property(v3_server, v3_settings_response):
    """Test that setting an invalid property raises a ValueError."""
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal"
        ),
        status=200,
        body=v3_settings_response,
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(ValueError):
            await system.set_properties({"Fake": "News"})


async def test_set_max_user_pins(v3_server, v3_settings_response):
    """Test throwing an error when setting too many user PINs."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=true"
        ),
        status=200,
        body=load_fixture("v3_settings_full_pins_response.json"),
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/pins"
        ),
        status=200,
        body=v3_settings_response,
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await get_api(
                TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
            )

            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.set_pin("whatever", "8121")
            assert "Refusing to create more than" in str(err)


async def test_set_pin(v3_server, v3_settings_response):
    """Test setting a PIN in a V3 system."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=200,
        body=v3_settings_response,
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=true"
        ),
        status=200,
        body=v3_settings_response,
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/pins"
        ),
        status=200,
        body=load_fixture("v3_settings_new_pin_response.json"),
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=200,
        body=load_fixture("v3_settings_new_pin_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        latest_pins = await system.get_pins()
        assert len(latest_pins) == 4

        await system.set_pin("whatever", "1274")
        latest_pins = await system.get_pins()
        assert len(latest_pins) == 5


async def test_set_pin_wrong_chars(v3_server):
    """Test throwing an error when setting a PIN with non-digits."""
    async with aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await get_api(
                TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
            )

            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.set_pin("whatever", "abcd")
            assert "PINs can only contain numbers" in str(err)


async def test_set_pin_wrong_length(v3_server):
    """Test throwing an error when setting a PIN with the wrong length."""
    async with aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await get_api(
                TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
            )

            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.set_pin("whatever", "1122334455")
            assert "digits long" in str(err)


async def test_set_states(v3_server):
    """Test the ability to set the state of the system."""
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state/away"
        ),
        status=200,
        body=load_fixture("v3_state_away_response.json"),
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state/home"
        ),
        status=200,
        body=load_fixture("v3_state_home_response.json"),
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state/off"
        ),
        status=200,
        body=load_fixture("v3_state_off_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        await system.set_away()
        assert system.state == SystemStates.away

        await system.set_home()
        assert system.state == SystemStates.home

        await system.set_off()
        assert system.state == SystemStates.off


async def test_system_notifications(v3_server, v3_subscriptions_response):
    """Test getting system notifications."""
    v3_server.get(
        f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}",
        status=200,
        body=v3_subscriptions_response,
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        assert len(system.notifications) == 1
        notification1 = system.notifications[0]
        assert notification1.notification_id == "xxxxxxxxxxxxxxxxxxxxxxxx"
        assert notification1.text == "Power Outage - Backup battery in use."
        assert notification1.category == "error"
        assert notification1.code == "2000"
        assert notification1.received_dt == datetime(
            2020, 2, 16, 3, 20, 28, tzinfo=pytz.UTC
        )
        assert notification1.link == "http://link.to.info"
        assert notification1.link_label == "More Info"


async def test_unavailable_endpoint(v3_server):
    """Test that an unavailable endpoint logs a message."""
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=403,
        body=load_fixture("unavailable_endpoint_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(EndpointUnavailableError):
            await system.update(include_system=False, include_entities=False)


@pytest.mark.parametrize(
    "v3_subscriptions_response",
    ["subscriptions_unknown_state_response"],
    indirect=True,
)
async def test_unknown_initial_state(caplog, v3_server):
    """Test handling of an initially unknown state."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        await simplisafe.get_systems()
        assert any("Unknown system state" in e.message for e in caplog.records)
        assert any("NOT_REAL_STATE" in e.message for e in caplog.records)


async def test_update_system_data(
    v3_server, v3_subscriptions_response, v3_settings_response
):
    """Test getting updated data for a v3 system."""
    v3_server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_USER_ID}/subscriptions?activeOnly=true",
        status=200,
        body=v3_subscriptions_response,
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/sensors?forceUpdate=false"
        ),
        status=200,
        body=load_fixture("v3_sensors_response.json"),
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=200,
        body=v3_settings_response,
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        await system.update()

        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.system_id == TEST_SYSTEM_ID
        assert len(system.sensors) == 24


async def test_update_error(v3_server, v3_subscriptions_response, v3_settings_response):
    """Test handling a generic error during update."""
    v3_server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_USER_ID}/subscriptions?activeOnly=true",
        status=200,
        body=v3_subscriptions_response,
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/sensors?forceUpdate=false"
        ),
        status=200,
        body=load_fixture("v3_sensors_response.json"),
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/settings/normal?forceUpdate=false"
        ),
        status=500,
        body="Server Error",
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL,
            TEST_PASSWORD,
            session=session,
            client_id=TEST_CLIENT_ID,
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(RequestError):
            await system.update()
