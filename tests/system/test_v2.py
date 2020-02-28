"""Define tests for v2 System objects."""
import aiohttp
import pytest

from simplipy import API
from simplipy.system import SystemStates

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


@pytest.mark.asyncio
async def test_get_pins(aresponses, v2_server):
    """Test getting PINs associated with a V2 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
            "get",
            aresponses.Response(text=load_fixture("v2_pins_response.json"), status=200),
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
async def test_get_systems(aresponses, v2_server, v2_subscriptions_response):
    """Test the ability to get systems attached to a v2 account."""
    async with v2_server:
        # Since this flow will call both three routes once more each (on top of
        # what instantiation does) and aresponses deletes matches each time,
        # we need to add additional routes:
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(
                text=load_fixture("api_token_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            "/v1/api/authCheck",
            "get",
            aresponses.Response(
                text=load_fixture("auth_check_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v2_subscriptions_response, status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
            "get",
            aresponses.Response(
                text=load_fixture("v2_settings_response.json"), status=200
            ),
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
            assert len(system.sensors) == 35

            simplisafe = await API.login_via_token(TEST_REFRESH_TOKEN, websession)
            systems = await simplisafe.get_systems()
            assert len(systems) == 1

            system = systems[TEST_SYSTEM_ID]
            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert simplisafe.access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 35


@pytest.mark.asyncio
async def test_set_pin(aresponses, v2_server):
    """Test setting a PIN in a V2 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
            "get",
            aresponses.Response(text=load_fixture("v2_pins_response.json"), status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
            "get",
            aresponses.Response(text=load_fixture("v2_pins_response.json"), status=200),
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
            aresponses.Response(
                text=load_fixture("v2_new_pins_response.json"), status=200
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

            await system.set_pin("whatever", "1275")
            new_pins = await system.get_pins()
            assert len(new_pins) == 5


@pytest.mark.asyncio
async def test_set_states(aresponses, v2_server):
    """Test the ability to set the state of a v2 system."""
    async with v2_server:
        # Since this flow will make the same API call four times and
        # aresponses deletes matches each time, we need to add four additional
        # routes:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v2_state_away_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v2_state_home_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v2_state_off_response.json"), status=200
            ),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v2_state_off_response.json"), status=200
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
async def test_update_system_data(aresponses, v2_server, v2_subscriptions_response):
    """Test getting updated data for a v2 system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            aresponses.Response(text=v2_subscriptions_response, status=200),
        )
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
            "get",
            aresponses.Response(
                text=load_fixture("v2_settings_response.json"), status=200
            ),
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
            assert len(system.sensors) == 35
