"""Define tests for v2 System objects."""
# pylint: disable=unused-argument
import aiohttp
import pytest

from simplipy import API
from simplipy.system import SystemStates

from tests.common import (
    TEST_AUTHORIZATION_CODE,
    TEST_CODE_VERIFIER,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
)


@pytest.mark.asyncio
async def test_get_pins(aresponses, v2_pins_response, v2_server):
    """Test getting PINs associated with a V2 system."""
    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
        "get",
        response=aiohttp.web_response.json_response(v2_pins_response, status=200),
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
        assert pins["Mother"] == "3456"
        assert pins["Father"] == "4567"

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_async_get_systems(aresponses, v2_server, v2_subscriptions_response):
    """Test the ability to get systems attached to a v2 account."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        assert len(systems) == 1

        system = systems[TEST_SYSTEM_ID]
        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.system_id == TEST_SYSTEM_ID
        assert len(system.sensors) == 35

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_pin(aresponses, v2_pins_response, v2_server, v2_settings_response):
    """Test setting a PIN in a V2 system."""
    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
        "get",
        response=aiohttp.web_response.json_response(v2_pins_response, status=200),
    )
    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
        "get",
        response=aiohttp.web_response.json_response(v2_pins_response, status=200),
    )
    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
        "post",
        response=aiohttp.web_response.json_response(v2_settings_response, status=200),
    )

    v2_pins_response["pins"]["pin4"]["value"] = "1275"
    v2_pins_response["pins"]["pin4"]["name"] = "whatever"

    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins",
        "get",
        response=aiohttp.web_response.json_response(v2_pins_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        latest_pins = await system.async_get_pins()
        assert len(latest_pins) == 4

        await system.async_set_pin("whatever", "1275")
        new_pins = await system.async_get_pins()
        assert len(new_pins) == 5

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_states(aresponses, v2_server, v2_state_response):
    """Test the ability to set the state of a v2 system."""
    v2_state_response["requestedState"] = "away"

    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v2_state_response, status=200),
    )

    v2_state_response["requestedState"] = "home"

    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v2_state_response, status=200),
    )

    v2_state_response["requestedState"] = "off"

    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v2_state_response, status=200),
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
async def test_update_system_data(
    aresponses, v2_server, v2_settings_response, v2_subscriptions_response
):
    """Test getting updated data for a v2 system."""
    v2_server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(
            v2_subscriptions_response, status=200
        ),
    )
    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings",
        "get",
        response=aiohttp.web_response.json_response(v2_settings_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.system_id == TEST_SYSTEM_ID
        assert len(system.sensors) == 35

        # If this succeeds without throwing an exception, the update is successful:
        await system.async_update()

    aresponses.assert_plan_strictly_followed()
