"""Define tests for v3 System objects."""
from datetime import datetime
import json
import logging

import aiohttp
import pytest
import pytz

from simplipy import API
from simplipy.errors import InvalidCredentialsError, PinError, SimplipyError
from simplipy.system import SystemStates
from simplipy.system.v3 import VOLUME_HIGH, VOLUME_MEDIUM

from tests.common import (
    TEST_ACCESS_TOKEN,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    TEST_USER_ID,
    load_fixture,
)


@pytest.fixture()
def subscriptions_alarm_state_response(subscriptions_fixture_filename):
    """Define a fixture for a subscription with an ALARM alarm state."""
    raw = load_fixture(subscriptions_fixture_filename)
    data = json.loads(raw)
    data["subscriptions"][0]["location"]["system"]["alarmState"] = "ALARM"
    return json.dumps(data)


@pytest.fixture()
def settings_missing_basestation_response(v3_settings_response):
    """Define a fixture for settings that are missing base station status."""
    data = json.loads(v3_settings_response)
    data["settings"].pop("basestationStatus")
    return json.dumps(data)


@pytest.fixture()
def subscriptions_missing_notifications_response(subscriptions_fixture_filename):
    """Define a fixture for a subscription that is missing notifications."""
    raw = load_fixture(subscriptions_fixture_filename)
    data = json.loads(raw)
    data["subscriptions"][0]["location"]["system"].pop("messages")
    return json.dumps(data)


@pytest.fixture()
def subscriptions_unknown_state_response(subscriptions_fixture_filename):
    """Define a fixture for a subscription with an unknown alarm state."""
    raw = load_fixture(subscriptions_fixture_filename)
    data = json.loads(raw)
    data["subscriptions"][0]["location"]["system"]["alarmState"] = "NOT_REAL_STATE"
    return json.dumps(data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "v3_subscriptions_response", ["subscriptions_alarm_state_response"], indirect=True,
)
async def test_alarm_state(v3_server):
    """Test handling of a triggered alarm."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            assert system.state == SystemStates.alarm


@pytest.mark.asyncio
async def test_get_last_event(aresponses, v3_server):
    """Test getting the latest event."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
            "get",
            aresponses.Response(
                text=load_fixture("latest_event_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            latest_event = await system.get_latest_event()
            assert latest_event["eventId"] == 1234567890


@pytest.mark.asyncio
async def test_get_pins(aresponses, v3_server, v3_settings_response):
    """Test getting PINs associated with a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            pins = await system.get_pins()
            assert len(pins) == 4
            assert pins["master"] == "1234"
            assert pins["duress"] == "9876"
            assert pins["Test 1"] == "3456"
            assert pins["Test 2"] == "5423"


@pytest.mark.asyncio
async def test_get_systems(
    aresponses, v3_server, v3_subscriptions_response, v3_settings_response
):
    """Test the ability to get systems attached to a v3 account."""
    async with v3_server:
        # Since this flow will call both three routes once more each (on top of
        # what instantiation does) and aresponses deletes matches each time,
        # we need to add additional routes:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("api_token_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(
                text=load_fixture("auth_check_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v3_subscriptions_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            aresponses.Response(
                text=load_fixture("v3_sensors_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            assert len(systems) == 1

            system = systems[TEST_SYSTEM_ID]

            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert simplisafe.access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 22

            simplisafe = await API.login_via_token(TEST_REFRESH_TOKEN, websession)
            systems = await simplisafe.get_systems()
            assert len(systems) == 1

            system = systems[TEST_SYSTEM_ID]

            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert simplisafe.access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 22


@pytest.mark.asyncio
async def test_empty_events(aresponses, v3_server):
    """Test that an empty events structure is handled correctly."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
            "get",
            aresponses.Response(
                text=load_fixture("events_empty_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            # Test the events key existing, but being empty:
            with pytest.raises(SimplipyError):
                _ = await system.get_latest_event()


@pytest.mark.asyncio
async def test_missing_events(aresponses, v3_server):
    """Test that an altogether-missing events structure is handled correctly."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
            "get",
            aresponses.Response(
                text=load_fixture("events_missing_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            # Test the events key existing, but being empty:
            with pytest.raises(SimplipyError):
                _ = await system.get_latest_event()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "v3_subscriptions_response",
    ["subscriptions_missing_notifications_response"],
    indirect=True,
)
async def test_no_notifications_in_basic_plan(caplog, v3_server):
    """Test that missing notification data is handled correctly."""
    caplog.set_level(logging.INFO)

    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            assert system.notifications == []
            assert any(
                "Notifications unavailable in plan" in e.message for e in caplog.records
            )


@pytest.mark.asyncio
async def test_no_state_change_on_failure(aresponses, v3_server):
    """Test that the system doesn't change state on an error."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
            "post",
            aresponses.Response(text=None, status=401),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text="", status=401),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            assert system.state == SystemStates.off

            with pytest.raises(InvalidCredentialsError):
                await system.set_away()
            assert system.state == SystemStates.off


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "v3_settings_response", ["settings_missing_basestation_response"],
)
async def test_missing_base_station_data(caplog, v3_server):
    """Test that missing base station data is handled correctly."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            assert system.gsm_strength is None
            assert any(
                "SimpliSafe cloud didn't return expected data for property" in e.message
                for e in caplog.records
            )


@pytest.mark.asyncio
async def test_properties(aresponses, v3_server, v3_settings_response):
    """Test that v3 system properties are available."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
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
            system.settings_info["settings"]["normal"]["alarmDuration"] = 0
            system.settings_info["settings"]["normal"]["alarmVolume"] = 0
            system.settings_info["settings"]["normal"]["doorChime"] = 0
            system.settings_info["settings"]["normal"]["entryDelayAway"] = 0
            system.settings_info["settings"]["normal"]["entryDelayHome"] = 0
            system.settings_info["settings"]["normal"]["exitDelayAway"] = 0
            system.settings_info["settings"]["normal"]["exitDelayHome"] = 1000
            system.settings_info["settings"]["normal"]["light"] = False
            system.settings_info["settings"]["normal"]["voicePrompts"] = 0

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


@pytest.mark.asyncio
async def test_remove_nonexistent_pin(aresponses, v3_server, v3_settings_response):
    """Test throwing an error when removing a nonexistent PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            with pytest.raises(PinError) as err:
                await system.remove_pin("0000")
                assert "Refusing to delete nonexistent PIN" in str(err)


@pytest.mark.asyncio
async def test_remove_pin(aresponses, v3_server, v3_settings_response):
    """Test removing a PIN in a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            aresponses.Response(
                text=load_fixture("v3_settings_deleted_pin_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(
                text=load_fixture("v3_settings_deleted_pin_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            latest_pins = await system.get_pins()
            assert len(latest_pins) == 4

            await system.remove_pin("Test 2")
            latest_pins = await system.get_pins()
            assert len(latest_pins) == 3


@pytest.mark.asyncio
async def test_remove_reserved_pin(aresponses, v3_server, v3_settings_response):
    """Test throwing an error when removing a reserved PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            with pytest.raises(PinError) as err:
                await system.remove_pin("master")
                assert "Refusing to delete reserved PIN" in str(err)


@pytest.mark.asyncio
async def test_set_duplicate_pin(aresponses, v3_server, v3_settings_response):
    """Test throwing an error when setting a duplicate PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            with pytest.raises(PinError) as err:
                simplisafe = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, websession
                )
                systems = await simplisafe.get_systems()
                system = systems[TEST_SYSTEM_ID]

                await system.set_pin("whatever", "1234")
                assert "Refusing to create duplicate PIN" in str(err)


@pytest.mark.asyncio
async def test_set_invalid_property(aresponses, v3_server, v3_settings_response):
    """Test that setting an invalid property raises a ValueError."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            with pytest.raises(ValueError):
                await system.set_properties({"Fake": "News"})


@pytest.mark.asyncio
async def test_set_max_user_pins(aresponses, v3_server, v3_settings_response):
    """Test throwing an error when setting too many user PINs."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(
                text=load_fixture("v3_settings_full_pins_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            with pytest.raises(PinError) as err:
                simplisafe = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, websession
                )
                systems = await simplisafe.get_systems()
                system = systems[TEST_SYSTEM_ID]

                await system.set_pin("whatever", "8121")
                assert "Refusing to create more than" in str(err)


@pytest.mark.asyncio
async def test_set_pin(aresponses, v3_server, v3_settings_response):
    """Test setting a PIN in a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            aresponses.Response(
                text=load_fixture("v3_settings_new_pin_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(
                text=load_fixture("v3_settings_new_pin_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            latest_pins = await system.get_pins()
            assert len(latest_pins) == 4

            await system.set_pin("whatever", "1274")
            latest_pins = await system.get_pins()
            assert len(latest_pins) == 5


@pytest.mark.asyncio
async def test_set_pin_wrong_chars(v3_server):
    """Test throwing an error when setting a PIN with non-digits."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            with pytest.raises(PinError) as err:
                simplisafe = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, websession
                )
                systems = await simplisafe.get_systems()
                system = systems[TEST_SYSTEM_ID]

                await system.set_pin("whatever", "abcd")
                assert "PINs can only contain numbers" in str(err)


@pytest.mark.asyncio
async def test_set_pin_wrong_length(v3_server):
    """Test throwing an error when setting a PIN with the wrong length."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            with pytest.raises(PinError) as err:
                simplisafe = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, websession
                )
                systems = await simplisafe.get_systems()
                system = systems[TEST_SYSTEM_ID]

                await system.set_pin("whatever", "1122334455")
                assert "digits long" in str(err)


@pytest.mark.asyncio
async def test_set_states(aresponses, v3_server):
    """Test the ability to set the state of the system."""
    async with v3_server:
        # Since this flow will make the same API call four times and
        # aresponses deletes matches each time, we need to add four additional
        # routes:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
            "post",
            aresponses.Response(
                text=load_fixture("v3_state_away_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/home",
            "post",
            aresponses.Response(
                text=load_fixture("v3_state_home_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/off",
            "post",
            aresponses.Response(
                text=load_fixture("v3_state_off_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/off",
            "post",
            aresponses.Response(
                text=load_fixture("v3_state_off_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.set_away()
            assert system.state == SystemStates.away

            await system.set_home()
            assert system.state == SystemStates.home

            await system.set_off()
            assert system.state == SystemStates.off

            await system.set_off()
            assert system.state == SystemStates.off


@pytest.mark.asyncio
async def test_system_notifications(aresponses, v3_server, v3_subscriptions_response):
    """Test getting system notifications."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v3_subscriptions_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            assert len(system.notifications) == 1
            notification1 = system.notifications[0]
            assert notification1.notification_id == "xxxxxxxxxxxxxxxxxxxxxxxx"
            assert notification1.text == "Power Outage - Backup battery in use."
            assert notification1.category == "error"
            assert notification1.code == "2000"
            assert notification1.timestamp == datetime(
                2020, 2, 16, 3, 20, 28, tzinfo=pytz.UTC
            )
            assert notification1.link == "http://link.to.info"
            assert notification1.link_label == "More Info"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "v3_subscriptions_response",
    ["subscriptions_unknown_state_response"],
    indirect=True,
)
async def test_unknown_initial_state(caplog, v3_server):
    """Test handling of an initially unknown state."""
    async with v3_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            _ = await simplisafe.get_systems()
            assert any("Unknown system state" in e.message for e in caplog.records)
            assert any("NOT_REAL_STATE" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_update_system_data(
    aresponses, v3_server, v3_subscriptions_response, v3_settings_response
):
    """Test getting updated data for a v3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v3_subscriptions_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            aresponses.Response(
                text=load_fixture("v3_sensors_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.update()

            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert simplisafe.access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 22


@pytest.mark.asyncio
async def test_update_error(
    aresponses, v3_server, v3_subscriptions_response, v3_settings_response
):
    """Test handling a generic error during update."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v3_subscriptions_response, status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            aresponses.Response(
                text=load_fixture("v3_sensors_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=v3_settings_response, status=500),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            with pytest.raises(SimplipyError):
                await system.update()
