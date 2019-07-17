"""Define tests for the System object."""
# pylint: disable=protected-access,redefined-outer-name,too-many-arguments

import json

import aiohttp
import aresponses
import pytest

from simplipy import API
from simplipy.errors import PinError
from simplipy.system import System, SystemStates

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
from .fixtures import *  # noqa
from .fixtures.v2 import *  # noqa
from .fixtures.v3 import *  # noqa


@pytest.mark.asyncio
async def test_get_events(events_json, event_loop, v2_server):
    """Test getting events from a system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/events".format(TEST_SYSTEM_ID),
            "get",
            aresponses.Response(text=json.dumps(events_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            events = await system.get_events(1534725051, 2)

            assert len(events) == 2


@pytest.mark.asyncio
async def test_get_pins_v2(event_loop, v2_pins_json, v2_server):
    """Test getting PINs associated with a V3 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_pins_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            pins = await system.get_pins()
            assert len(pins) == 4
            assert pins["master"] == "1234"
            assert pins["duress"] == "9876"
            assert pins["Mother"] == "3456"
            assert pins["Father"] == "4567"


@pytest.mark.asyncio
async def test_get_pins_v3(event_loop, v3_server, v3_settings_json):
    """Test getting PINs associated with a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            pins = await system.get_pins()
            assert len(pins) == 4
            assert pins["master"] == "1234"
            assert pins["duress"] == "9876"
            assert pins["Test 1"] == "3456"
            assert pins["Test 2"] == "5423"


@pytest.mark.asyncio
async def test_get_systems_v2(
    api_token_json,
    auth_check_json,
    event_loop,
    v2_server,
    v2_settings_json,
    v2_subscriptions_json,
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
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_subscriptions_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/settings".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            credentials_api = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await credentials_api.get_systems()

            assert len(systems) == 1

            primary_system = systems[0]

            assert primary_system.serial == TEST_SYSTEM_SERIAL_NO
            assert primary_system.system_id == TEST_SYSTEM_ID
            assert primary_system.api._access_token == TEST_ACCESS_TOKEN
            assert len(primary_system.sensors) == 35

            token_api = await API.login_via_token(TEST_REFRESH_TOKEN, websession)
            systems = await token_api.get_systems()

            assert len(systems) == 1

            primary_system = systems[0]

            assert primary_system.serial == TEST_SYSTEM_SERIAL_NO
            assert primary_system.system_id == TEST_SYSTEM_ID
            assert primary_system.api._access_token == TEST_ACCESS_TOKEN
            assert len(primary_system.sensors) == 35


@pytest.mark.asyncio
async def test_get_systems_v3(
    api_token_json,
    auth_check_json,
    event_loop,
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
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_subscriptions_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/sensors".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_sensors_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            credentials_api = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, websession
            )
            systems = await credentials_api.get_systems()

            assert len(systems) == 1

            primary_system = systems[0]

            assert primary_system.serial == TEST_SYSTEM_SERIAL_NO
            assert primary_system.system_id == TEST_SYSTEM_ID
            assert primary_system.api._access_token == TEST_ACCESS_TOKEN
            assert len(primary_system.sensors) == 21

            token_api = await API.login_via_token(TEST_REFRESH_TOKEN, websession)
            systems = await token_api.get_systems()

            assert len(systems) == 1

            primary_system = systems[0]

            assert primary_system.serial == TEST_SYSTEM_SERIAL_NO
            assert primary_system.system_id == TEST_SYSTEM_ID
            assert primary_system.api._access_token == TEST_ACCESS_TOKEN
            assert len(primary_system.sensors) == 21


@pytest.mark.asyncio
async def test_remove_nonexistent_pin_v3(event_loop, v3_server, v3_settings_json):
    """Test throwing an error when removing a nonexistent PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            with pytest.raises(PinError) as err:
                await system.remove_pin("0000")
                assert "Refusing to delete nonexistent PIN" in str(err)


@pytest.mark.asyncio
async def test_remove_pin_v3(
    event_loop, v3_server, v3_settings_json, v3_settings_deleted_pin_json
):
    """Test removing a PIN in a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(
                text=json.dumps(v3_settings_deleted_pin_json), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(
                text=json.dumps(v3_settings_deleted_pin_json), status=200
            ),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            latest_pins = await system.get_pins()
            assert len(latest_pins) == 4

            await system.remove_pin("Test 2")
            latest_pins = await system.get_pins()
            assert len(latest_pins) == 3


@pytest.mark.asyncio
async def test_remove_reserved_pin_v3(event_loop, v3_server, v3_settings_json):
    """Test throwing an error when removing a reserved PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            with pytest.raises(PinError) as err:
                await system.remove_pin("master")
                assert "Refusing to delete reserved PIN" in str(err)


@pytest.mark.asyncio
async def test_set_duplicate_pin(event_loop, v3_server, v3_settings_json):
    """Test throwing an error when setting a duplicate PIN."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            with pytest.raises(PinError) as err:
                api = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, websession
                )
                [system] = await api.get_systems()

                await system.set_pin("whatever", "1234")
                assert "Refusing to create duplicate PIN" in str(err)


@pytest.mark.asyncio
async def test_set_max_user_pins(
    event_loop, v3_server, v3_settings_json, v3_settings_full_pins_json
):
    """Test throwing an error when setting too many user PINs."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(
                text=json.dumps(v3_settings_full_pins_json), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            with pytest.raises(PinError) as err:
                api = await API.login_via_credentials(
                    TEST_EMAIL, TEST_PASSWORD, websession
                )
                [system] = await api.get_systems()

                await system.set_pin("whatever", "8121")
                assert "Refusing to create more than" in str(err)


@pytest.mark.asyncio
async def test_set_pins_v2(event_loop, v2_new_pins_json, v2_pins_json, v2_server):
    """Test setting a PIN in a V2 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_pins_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_pins_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/pins".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=None, status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_new_pins_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            latest_pins = await system.get_pins()
            assert len(latest_pins) == 4

            await system.set_pin("whatever", "1275")
            new_pins = await system.get_pins()
            assert len(new_pins) == 5


@pytest.mark.asyncio
async def test_set_pin_v3(
    event_loop, v3_server, v3_settings_json, v3_settings_new_pin_json
):
    """Test setting a PIN in a V3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=json.dumps(v3_settings_new_pin_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_new_pin_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            latest_pins = await system.get_pins()
            assert len(latest_pins) == 4

            await system.set_pin("whatever", "1274")
            latest_pins = await system.get_pins()
            assert len(latest_pins) == 5


@pytest.mark.asyncio
async def test_properties(event_loop, v2_server):
    """Test that base system properties are created properly."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            assert system.address == TEST_ADDRESS
            assert not system.alarm_going_off
            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.state == SystemStates.off
            assert system.system_id == TEST_SYSTEM_ID
            assert system.temperature == 67
            assert system.version == 2


@pytest.mark.asyncio
async def test_properties_v3(event_loop, v3_server):
    """Test that v3 system properties are available."""
    async with v3_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            assert system.alarm_duration == 240
            assert system.alarm_volume == 3
            assert system.battery_backup_power_level == 5293
            assert system.entry_delay_away == 30
            assert system.entry_delay_home == 30
            assert system.exit_delay_away == 60
            assert system.exit_delay_home == 0
            assert system.gsm_strength == -73
            assert system.light is True
            assert system.rf_jamming is False
            assert system.voice_prompt_volume == 2
            assert system.wall_power_level == 5933
            assert system.wifi_ssid == "MY_WIFI"
            assert system.wifi_strength == -49


@pytest.mark.asyncio
async def test_set_states_v2(
    event_loop, v2_server, v2_state_away_json, v2_state_home_json, v2_state_off_json
):
    """Test the ability to set the state of a v2 system."""
    async with v2_server:
        # Since this flow will make the same API call four times and
        # aresponses deletes matches each time, we need to add four additional
        # routes:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/state".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=json.dumps(v2_state_away_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/state".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=json.dumps(v2_state_home_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/state".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=json.dumps(v2_state_off_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/state".format(TEST_SUBSCRIPTION_ID),
            "post",
            aresponses.Response(text=json.dumps(v2_state_off_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

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
    event_loop, v3_server, v3_state_away_json, v3_state_home_json, v3_state_off_json
):
    """Test the ability to set the state of the system."""
    async with v3_server:
        # Since this flow will make the same API call four times and
        # aresponses deletes matches each time, we need to add four additional
        # routes:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/state/{1}".format(TEST_SUBSCRIPTION_ID, "away"),
            "post",
            aresponses.Response(text=json.dumps(v3_state_away_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/state/{1}".format(TEST_SUBSCRIPTION_ID, "home"),
            "post",
            aresponses.Response(text=json.dumps(v3_state_home_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/state/{1}".format(TEST_SUBSCRIPTION_ID, "off"),
            "post",
            aresponses.Response(text=json.dumps(v3_state_off_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/state/{1}".format(TEST_SUBSCRIPTION_ID, "off"),
            "post",
            aresponses.Response(text=json.dumps(v3_state_off_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            await system.set_away()
            assert system.state == SystemStates.away

            await system.set_home()
            assert system.state == SystemStates.home

            await system.set_off()
            assert system.state == SystemStates.off

            await system.set_off()
            assert system.state == SystemStates.off


@pytest.mark.asyncio
async def test_unknown_initial_state(caplog, event_loop):
    """Test handling of an initially unknown state."""
    async with aiohttp.ClientSession(loop=event_loop) as websession:
        _ = System(API(websession), {"system": {"alarmState": "fake"}})  # noqa

        assert any("Unknown" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_unknown_sensor_type(caplog, event_loop, v2_server):
    """Test whether a message is logged upon finding an unknown sensor type."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            _ = await api.get_systems()  # noqa

            assert any("Unknown" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_update_system_data_v2(
    event_loop, v2_server, v2_settings_json, v2_subscriptions_json
):
    """Test getting updated data for a v2 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_subscriptions_json), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/subscriptions/{0}/settings".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v2_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            await system.update()

            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert system.api._access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 35


@pytest.mark.asyncio
async def test_update_system_data_v3(
    event_loop, v3_server, v3_sensors_json, v3_settings_json, v3_subscriptions_json
):
    """Test getting updated data for a v3 system."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_subscriptions_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/sensors".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_sensors_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=200),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            await system.update()

            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert system.api._access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 21


@pytest.mark.asyncio
async def test_update_error_v3(
    caplog,
    event_loop,
    v3_server,
    v3_sensors_json,
    v3_settings_json,
    v3_subscriptions_json,
):
    """Test handling a generic error during update."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            "/v1/users/{0}/subscriptions".format(TEST_USER_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_subscriptions_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/sensors".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_sensors_json), status=200),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/ss3/subscriptions/{0}/settings/pins".format(TEST_SUBSCRIPTION_ID),
            "get",
            aresponses.Response(text=json.dumps(v3_settings_json), status=500),
        )

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            [system] = await api.get_systems()

            await system.update()

            assert any(
                "Error while retrieving settings" in e.message for e in caplog.records
            )
