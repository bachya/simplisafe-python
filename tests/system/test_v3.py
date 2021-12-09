"""Define tests for v3 System objects."""
# pylint: disable=protected-access,too-many-arguments,unused-argument
from datetime import datetime, timedelta
import logging

import aiohttp
import pytest
import pytz

from simplipy import API
from simplipy.errors import (
    EndpointUnavailableError,
    InvalidCredentialsError,
    PinError,
    RequestError,
    SimplipyError,
)
from simplipy.system import SystemStates
from simplipy.system.v3 import Volume

from tests.common import (
    TEST_AUTHORIZATION_CODE,
    TEST_CODE_VERIFIER,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    TEST_USER_ID,
)


@pytest.mark.asyncio
async def test_alarm_state(aresponses, v3_server):
    """Test that we can get the alarm state."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert system.state == SystemStates.OFF

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_clear_notifications(aresponses, v3_server, v3_settings_response):
    """Test clearing all active notifications."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/messages",
        "delete",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        await system.async_clear_notifications()
        assert system.notifications == []

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_get_last_event(aresponses, latest_event_response, v3_server):
    """Test getting the latest event."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
        "get",
        response=aiohttp.web_response.json_response(latest_event_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        latest_event = await system.async_get_latest_event()
        assert latest_event["eventId"] == 1234567890

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_get_pins(aresponses, v3_server, v3_settings_response):
    """Test getting PINs associated with a V3 system."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        pins = await system.async_get_pins()
        assert len(pins) == 4
        assert pins["master"] == "1234"
        assert pins["duress"] == "9876"
        assert pins["Test 1"] == "3456"
        assert pins["Test 2"] == "5423"

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_async_get_systems(aresponses, v3_server):
    """Test the ability to get systems attached to a v3 account."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        assert len(systems) == 1

        system = systems[TEST_SYSTEM_ID]
        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.system_id == TEST_SYSTEM_ID
        assert len(system.sensors) == 24

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_empty_events(aresponses, events_response, v3_server):
    """Test that an empty events structure is handled correctly."""
    events_response["events"] = []

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
        "get",
        response=aiohttp.web_response.json_response(events_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        # Test the events key existing, but being empty:
        with pytest.raises(SimplipyError):
            _ = await system.async_get_latest_event()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_lock_state_update_bug(aresponses, caplog, v3_server, v3_state_response):
    """Test halting updates within a 15-second window from arming/disarming."""
    caplog.set_level(logging.INFO)

    v3_state_response["state"] = "AWAY"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
        "post",
        response=aiohttp.web_response.json_response(v3_state_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        await system.async_set_away()
        assert system.state == SystemStates.AWAY

        await system.async_update()
        assert any("Skipping system update" in e.message for e in caplog.records)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_missing_events(aresponses, events_response, v3_server):
    """Test that an altogether-missing events structure is handled correctly."""
    events_response.pop("events")

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
        "get",
        response=aiohttp.web_response.json_response(events_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        # Test the events key existing, but being empty:
        with pytest.raises(SimplipyError):
            _ = await system.async_get_latest_event()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_no_state_change_on_failure(aresponses, v3_server):
    """Test that the system doesn't change state on an error."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
        "post",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    v3_server.add(
        "auth.simplisafe.com",
        "/oauth/token",
        "post",
        response=aresponses.Response(text="Unauthorized", status=401),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )

        # Manually set the expiration datetime to force a refresh token flow:
        simplisafe._token_last_refreshed = datetime.utcnow() + timedelta(seconds=30)

        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert system.state == SystemStates.OFF

        with pytest.raises(InvalidCredentialsError):
            await system.async_set_away()
        assert system.state == SystemStates.OFF

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_properties(aresponses, v3_server, v3_settings_response):
    """Test that v3 system properties are available."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "post",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert system.alarm_duration == 240
        assert system.alarm_volume == Volume.HIGH
        assert system.battery_backup_power_level == 5293
        assert system.chime_volume == Volume.MEDIUM
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
        assert system.voice_prompt_volume == Volume.MEDIUM
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

        await system.async_set_properties(
            {
                "alarm_duration": 240,
                "alarm_volume": Volume.HIGH,
                "chime_volume": Volume.MEDIUM,
                "entry_delay_away": 30,
                "entry_delay_home": 30,
                "exit_delay_away": 60,
                "exit_delay_home": 0,
                "light": True,
                "voice_prompt_volume": Volume.MEDIUM,
            }
        )
        assert system.alarm_duration == 240
        assert system.alarm_volume == Volume.HIGH
        assert system.chime_volume == Volume.MEDIUM
        assert system.entry_delay_away == 30
        assert system.entry_delay_home == 30
        assert system.exit_delay_away == 60
        assert system.exit_delay_home == 0
        assert system.light is True
        assert system.voice_prompt_volume == Volume.MEDIUM

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_remove_nonexistent_pin(aresponses, v3_server, v3_settings_response):
    """Test throwing an error when removing a nonexistent PIN."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(PinError) as err:
            await system.async_remove_pin("0000")
            assert "Refusing to delete nonexistent PIN" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_remove_pin(aresponses, v3_server, v3_settings_response):
    """Test removing a PIN in a V3 system."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    v3_settings_response["settings"]["pins"]["users"][1]["pin"] = ""
    v3_settings_response["settings"]["pins"]["users"][1]["name"] = ""

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
        "post",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        latest_pins = await system.async_get_pins()
        assert len(latest_pins) == 4

        await system.async_remove_pin("Test 2")
        latest_pins = await system.async_get_pins()
        assert len(latest_pins) == 3

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_remove_reserved_pin(aresponses, v3_server, v3_settings_response):
    """Test throwing an error when removing a reserved PIN."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(PinError) as err:
            await system.async_remove_pin("master")
            assert "Refusing to delete reserved PIN" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_duplicate_pin(aresponses, v3_server, v3_settings_response):
    """Test throwing an error when setting a duplicate PIN."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
        "post",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.async_set_pin("whatever", "1234")
            assert "Refusing to create duplicate PIN" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_invalid_property(aresponses, v3_server, v3_settings_response):
    """Test that setting an invalid property raises a ValueError."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "post",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(ValueError):
            await system.async_set_properties({"Fake": "News"})

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_max_user_pins(
    aresponses,
    subscriptions_response,
    v3_server,
    v3_settings_response,
):
    """Test throwing an error when setting too many user PINs."""
    v3_settings_response["settings"]["pins"]["users"] = [
        {
            "_id": "1271279d966212121124c6",
            "pin": "1234",
            "name": "Test 1",
        },
        {
            "_id": "1271279d966212121124c7",
            "pin": "5678",
            "name": "Test 2",
        },
        {
            "_id": "1271279d966212121124c8",
            "pin": "9012",
            "name": "Test 3",
        },
        {
            "_id": "1271279d966212121124c9",
            "pin": "3456",
            "name": "Test 4",
        },
    ]

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
        "post",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.async_set_pin("whatever", "8121")
            assert "Refusing to create more than" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_pin(aresponses, v3_server, v3_settings_response):
    """Test setting a PIN in a V3 system."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    v3_settings_response["settings"]["pins"]["users"][2]["pin"] = "1274"
    v3_settings_response["settings"]["pins"]["users"][2]["name"] = "whatever"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
        "post",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        latest_pins = await system.async_get_pins()
        assert len(latest_pins) == 4

        await system.async_set_pin("whatever", "1274")
        latest_pins = await system.async_get_pins()
        assert len(latest_pins) == 5

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_pin_wrong_chars(aresponses, v3_server):
    """Test throwing an error when setting a PIN with non-digits."""
    async with aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.async_set_pin("whatever", "abcd")
            assert "PINs can only contain numbers" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_pin_wrong_length(aresponses, v3_server):
    """Test throwing an error when setting a PIN with the wrong length."""
    async with aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.async_set_pin("whatever", "1122334455")
            assert "digits long" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_states(aresponses, v3_server, v3_state_response):
    """Test the ability to set the state of the system."""
    v3_state_response["state"] = "AWAY"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
        "post",
        response=aiohttp.web_response.json_response(v3_state_response, status=200),
    )

    v3_state_response["state"] = "HOME"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/home",
        "post",
        response=aiohttp.web_response.json_response(v3_state_response, status=200),
    )

    v3_state_response["state"] = "OFF"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/off",
        "post",
        response=aiohttp.web_response.json_response(v3_state_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        await system.async_set_away()
        assert system.state == SystemStates.AWAY

        await system.async_set_home()
        assert system.state == SystemStates.HOME

        await system.async_set_off()
        assert system.state == SystemStates.OFF

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_system_notifications(aresponses, v3_server):
    """Test getting system notifications."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
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

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unavailable_endpoint(
    aresponses, unavailable_endpoint_response, v3_server
):
    """Test that an unavailable endpoint logs a message."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(
            unavailable_endpoint_response, status=403
        ),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(EndpointUnavailableError):
            await system.async_update(include_subscription=False, include_devices=False)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_update_system_data(
    aresponses,
    subscriptions_response,
    v3_sensors_response,
    v3_server,
    v3_settings_response,
):
    """Test getting updated data for a v3 system."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_USER_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(subscriptions_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
        "get",
        response=aiohttp.web_response.json_response(v3_sensors_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        await system.async_update()

        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.system_id == TEST_SYSTEM_ID
        assert len(system.sensors) == 24

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_update_error(
    aresponses,
    subscriptions_response,
    v3_sensors_response,
    v3_server,
    v3_settings_response,
):
    """Test handling a generic error during update."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_USER_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(subscriptions_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
        "get",
        response=aresponses.Response(text="Server Error", status=500),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE,
            TEST_CODE_VERIFIER,
            session=session,
            # Set so that our tests don't take too long:
            request_retries=1,
        )

        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        with pytest.raises(RequestError):
            await system.async_update()

    aresponses.assert_plan_strictly_followed()
