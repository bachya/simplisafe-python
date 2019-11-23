"""Define tests for the System object."""
# pylint: disable=protected-access,redefined-outer-name,unused-import
import json

import aiohttp
import aresponses
import pytest

from simplipy import API
from simplipy.errors import InvalidCredentialsError, PinError
from simplipy.system import System, SystemStates
from simplipy.system.v3 import LevelMap as V3LevelMap

from .common import async_mock
from .const import (
    TEST_ACCESS_TOKEN,
    TEST_ADDRESS,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    TEST_USER_ID,
)
from .fixtures import (  # noqa
    api_token_json,
    auth_check_json,
    events_json,
    latest_event_json,
)
from .fixtures.v2 import (  # noqa
    v2_new_pins_json,
    v2_pins_json,
    v2_server,
    v2_settings_json,
    v2_state_away_json,
    v2_state_home_json,
    v2_state_off_json,
    v2_subscriptions_json,
)
from .fixtures.v3 import (  # noqa
    v3_sensors_json,
    v3_server,
    v3_settings_deleted_pin_json,
    v3_settings_json,
    v3_settings_full_pins_json,
    v3_settings_new_pin_json,
    v3_state_away_json,
    v3_state_home_json,
    v3_state_off_json,
    v3_subscriptions_json,
)


@pytest.mark.asyncio
async def test_get_events(events_json, v2_server):
    """Test getting events from a system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SYSTEM_ID}/events",
            "get",
            aresponses.Response(text=json.dumps(events_json), status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            events = await system.get_events(1534725051, 2)

            assert len(events) == 2


@pytest.mark.asyncio
async def test_get_last_event(v3_server, latest_event_json):
    """Test getting the latest event."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
            "get",
            aresponses.Response(text=json.dumps(latest_event_json), status=200),
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
async def test_get_pins_v2(v2_pins_json, v2_server):
    """Test getting PINs associated with a V3 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
            "get",
            aresponses.Response(text=json.dumps(v2_pins_json), status=200),
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
            assert pins["Mother"] == "3456"
            assert pins["Father"] == "4567"


@pytest.mark.asyncio
async def test_get_pins_v3(v3_server, v3_settings_json):
    """Test getting PINs associated with a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
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
async def test_get_systems_v2(  # pylint: disable=too-many-arguments
    api_token_json, auth_check_json, v2_server, v2_settings_json, v2_subscriptions_json
):
    """Test the ability to get systems attached to a v2 account."""
    async with v2_server:
        # Since this flow will call both three routes once more each (on top of
        # what instantiation does) and aresponses deletes matches each time,
        # we need to add additional routes:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text=json.dumps(api_token_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=json.dumps(v2_subscriptions_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
            "get",
            aresponses.Response(text=json.dumps(v2_settings_json), status=200),
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
            assert simplisafe._access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 35

            simplisafe = await API.login_via_token(TEST_REFRESH_TOKEN, websession)
            systems = await simplisafe.get_systems()
            assert len(systems) == 1

            system = systems[TEST_SYSTEM_ID]
            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert simplisafe._access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 35


@pytest.mark.asyncio
async def test_get_systems_v3(  # pylint: disable=too-many-arguments
    api_token_json,
    auth_check_json,
    v3_sensors_json,
    v3_server,
    v3_settings_json,
    v3_subscriptions_json,
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
            aresponses.Response(text=json.dumps(api_token_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(text=json.dumps(auth_check_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=json.dumps(v3_subscriptions_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            aresponses.Response(text=json.dumps(v3_sensors_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
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
            assert simplisafe._access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 22

            simplisafe = await API.login_via_token(TEST_REFRESH_TOKEN, websession)
            systems = await simplisafe.get_systems()
            assert len(systems) == 1

            system = systems[TEST_SYSTEM_ID]

            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert simplisafe._access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 22


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
async def test_remove_nonexistent_pin_v3(v3_server, v3_settings_json):
    """Test throwing an error when removing a nonexistent PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
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
async def test_remove_pin_v3(v3_server, v3_settings_json, v3_settings_deleted_pin_json):
    """Test removing a PIN in a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            aresponses.Response(
                text=json.dumps(v3_settings_deleted_pin_json), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(
                text=json.dumps(v3_settings_deleted_pin_json), status=200
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
async def test_remove_reserved_pin_v3(v3_server, v3_settings_json):
    """Test throwing an error when removing a reserved PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
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
async def test_set_duplicate_pin(v3_server, v3_settings_json):
    """Test throwing an error when setting a duplicate PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
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
async def test_properties(v2_server):
    """Test that base system properties are created properly."""
    async with v2_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            assert not system.alarm_going_off
            assert system.address == TEST_ADDRESS
            assert system.connection_type == "cell"
            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.state == SystemStates.off
            assert system.system_id == TEST_SYSTEM_ID
            assert system.temperature == 67
            assert system.version == 2


@pytest.mark.asyncio
async def test_properties_v3(v3_server, v3_settings_json):
    """Test that v3 system properties are available."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            assert system.alarm_duration == 240
            assert system.alarm_volume == V3LevelMap.high
            assert system.battery_backup_power_level == 5293
            assert system.chime_volume == V3LevelMap.medium
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
            assert system.voice_prompt_volume == V3LevelMap.medium
            assert system.wall_power_level == 5933
            assert system.wifi_ssid == "MY_WIFI"
            assert system.wifi_strength == -49

            # Test "setting" various system properties by overriding their values, then
            # calling the update functions:
            system._settings_info["settings"]["normal"]["alarmDuration"] = 0
            await system.set_alarm_duration(240)
            assert system.alarm_duration == 240

            system._settings_info["settings"]["normal"]["alarmVolume"] = 0
            await system.set_alarm_volume(V3LevelMap.high)
            assert system.alarm_volume == V3LevelMap.high

            system._settings_info["settings"]["normal"]["doorChime"] = 0
            await system.set_chime_volume(V3LevelMap.medium)
            assert system.chime_volume == V3LevelMap.medium

            system._settings_info["settings"]["normal"]["entryDelayAway"] = 0
            await system.set_entry_delay_away(30)
            assert system.entry_delay_away == 30

            system._settings_info["settings"]["normal"]["entryDelayHome"] = 0
            await system.set_entry_delay_home(30)
            assert system.entry_delay_home == 30

            system._settings_info["settings"]["normal"]["exitDelayAway"] = 0
            await system.set_exit_delay_away(60)
            assert system.exit_delay_away == 60

            system._settings_info["settings"]["normal"]["exitDelayHome"] = 1000
            await system.set_exit_delay_home(0)
            assert system.exit_delay_home == 0

            system._settings_info["settings"]["normal"]["light"] = False
            await system.set_light(True)
            assert system.exit_delay_home == 0

            system._settings_info["settings"]["normal"]["voicePrompts"] = 0
            await system.set_voice_prompt_volume(V3LevelMap.medium)
            assert system.voice_prompt_volume == V3LevelMap.medium


@pytest.mark.asyncio
async def test_set_max_user_pins(
    v3_server, v3_settings_json, v3_settings_full_pins_json
):
    """Test throwing an error when setting too many user PINs."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(
                text=json.dumps(v3_settings_full_pins_json), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
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
async def test_set_pin_v2(v2_new_pins_json, v2_pins_json, v2_server):
    """Test setting a PIN in a V2 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
            "get",
            aresponses.Response(text=json.dumps(v2_pins_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
            "get",
            aresponses.Response(text=json.dumps(v2_pins_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
            "post",
            aresponses.Response(text=None, status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
            "get",
            aresponses.Response(text=json.dumps(v2_new_pins_json), status=200),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            latest_pins = await system.get_pins()
            assert len(latest_pins) == 4

            await system.set_pin("whatever", "1275")
            new_pins = await system.get_pins()
            assert len(new_pins) == 5


@pytest.mark.asyncio
async def test_set_pin_v3(v3_server, v3_settings_json, v3_settings_new_pin_json):
    """Test setting a PIN in a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            aresponses.Response(text=json.dumps(v3_settings_new_pin_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_new_pin_json), status=200),
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
async def test_set_states_v2(
    v2_server, v2_state_away_json, v2_state_home_json, v2_state_off_json
):
    """Test the ability to set the state of a v2 system."""
    async with v2_server:
        # Since this flow will make the same API call four times and
        # aresponses deletes matches each time, we need to add four additional
        # routes:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(text=json.dumps(v2_state_away_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(text=json.dumps(v2_state_home_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(text=json.dumps(v2_state_off_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(text=json.dumps(v2_state_off_json), status=200),
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
async def test_set_states_v3(
    v3_server, v3_state_away_json, v3_state_home_json, v3_state_off_json
):
    """Test the ability to set the state of the system."""
    async with v3_server:
        # Since this flow will make the same API call four times and
        # aresponses deletes matches each time, we need to add four additional
        # routes:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
            "post",
            aresponses.Response(text=json.dumps(v3_state_away_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/home",
            "post",
            aresponses.Response(text=json.dumps(v3_state_home_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/off",
            "post",
            aresponses.Response(text=json.dumps(v3_state_off_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/off",
            "post",
            aresponses.Response(text=json.dumps(v3_state_off_json), status=200),
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
async def test_unknown_initial_state(caplog):
    """Test handling of an initially unknown state."""
    _ = System(async_mock, async_mock, {"system": {"alarmState": "fake"}})
    assert any("Unknown" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_unknown_sensor_type(caplog, v2_server):
    """Test whether a message is logged upon finding an unknown sensor type."""
    async with v2_server:
        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            _ = await simplisafe.get_systems()  # noqa

            assert any("Unknown" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_update_system_data_v2(
    v2_server, v2_settings_json, v2_subscriptions_json
):
    """Test getting updated data for a v2 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=json.dumps(v2_subscriptions_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
            "get",
            aresponses.Response(text=json.dumps(v2_settings_json), status=200),
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
            assert simplisafe._access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 35


@pytest.mark.asyncio
async def test_update_system_data_v3(
    v3_server, v3_sensors_json, v3_settings_json, v3_subscriptions_json
):
    """Test getting updated data for a v3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=json.dumps(v3_subscriptions_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            aresponses.Response(text=json.dumps(v3_sensors_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
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
            assert simplisafe._access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 22


@pytest.mark.asyncio
async def test_update_error_v3(  # pylint: disable=too-many-arguments
    caplog, v3_server, v3_sensors_json, v3_settings_json, v3_subscriptions_json
):
    """Test handling a generic error during update."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=json.dumps(v3_subscriptions_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            aresponses.Response(text=json.dumps(v3_sensors_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=500),
        )

        async with aiohttp.ClientSession() as websession:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.update()

            assert any(
                "Error while getting latest settings values" in e.message
                for e in caplog.records
            )
