"""Define tests for v2 System objects."""
import aiohttp
import pytest

from simplipy import get_api
from simplipy.system import SystemStates

from tests.common import (
    TEST_CLIENT_ID,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    load_fixture,
)


async def test_get_pins(v2_server):
    """Test getting PINs associated with a V2 system."""
    v2_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/pins?cached=true&settingsType=all"
        ),
        status=200,
        body=load_fixture("v2_pins_response.json"),
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
        assert pins["Mother"] == "3456"
        assert pins["Father"] == "4567"


async def test_get_systems(v2_server, v2_subscriptions_response):
    """Test the ability to get systems attached to a v2 account."""
    v2_server.post(
        "https://api.simplisafe.com/v1/api/token",
        status=200,
        body=load_fixture("api_token_response.json"),
    )
    v2_server.get(
        "https://api.simplisafe.com/v1/api/authCheck",
        status=200,
        body=load_fixture("auth_check_response.json"),
    )
    v2_server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=200,
        payload=v2_subscriptions_response,
    )
    v2_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings?"
            "cached=true&settingsType=all"
        ),
        status=200,
        body=load_fixture("v2_settings_response.json"),
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
        assert len(system.sensors) == 35


async def test_set_pin(v2_server):
    """Test setting a PIN in a V2 system."""
    v2_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/pins?cached=true&settingsType=all"
        ),
        status=200,
        body=load_fixture("v2_pins_response.json"),
    )
    v2_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/pins?cached=false&settingsType=all"
        ),
        status=200,
        body=load_fixture("v2_pins_response.json"),
    )
    v2_server.post(
        (f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/pins"),
        status=200,
        body=load_fixture("v2_settings_response.json"),
    )
    v2_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/pins?cached=true&settingsType=all"
        ),
        status=200,
        body=load_fixture("v2_new_pins_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        latest_pins = await system.get_pins()
        assert len(latest_pins) == 4

        await system.set_pin("whatever", "1275")
        new_pins = await system.get_pins()
        assert len(new_pins) == 5


async def test_set_states(v2_server):
    """Test the ability to set the state of a v2 system."""
    v2_server.post(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state?state=away"
        ),
        status=200,
        body=load_fixture("v2_state_away_response.json"),
    )
    v2_server.post(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state?state=home"
        ),
        status=200,
        body=load_fixture("v2_state_home_response.json"),
    )
    v2_server.post(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state?state=off"
        ),
        status=200,
        body=load_fixture("v2_state_off_response.json"),
    )
    v2_server.post(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}"
            "/state?state=off"
        ),
        status=200,
        body=load_fixture("v2_state_off_response.json"),
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

        await system.set_off()
        assert system.state == SystemStates.off


async def test_update_system_data(v2_server, v2_subscriptions_response):
    """Test getting updated data for a v2 system."""
    v2_server.get(
        f"https://api.simplisafe.com/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions?activeOnly=true",
        status=200,
        payload=v2_subscriptions_response,
    )
    v2_server.get(
        (
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/settings?"
            "cached=true&settingsType=all"
        ),
        status=200,
        body=load_fixture("v2_settings_response.json"),
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
        assert len(system.sensors) == 35
