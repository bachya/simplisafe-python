"""Define base tests for System objects."""
# pylint: disable=too-many-arguments,unused-argument
from datetime import datetime

import aiohttp
import pytest

from simplipy import API
from simplipy.system import SystemStates

from tests.common import (
    TEST_ADDRESS,
    TEST_AUTHORIZATION_CODE,
    TEST_CODE_VERIFIER,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    TEST_USER_ID,
)


@pytest.mark.asyncio
async def test_deactivated_system(aresponses, server, subscriptions_response):
    """Test that API.async_get_systems doesn't return deactivated systems."""
    subscriptions_response["subscriptions"][0]["activated"] = 0

    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(subscriptions_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        assert len(systems) == 0

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_get_events(aresponses, events_response, v2_server):
    """Test getting events from a system."""
    v2_server.add(
        "api.simplisafe.com",
        f"/v1/subscriptions/{TEST_SYSTEM_ID}/events",
        "get",
        response=aiohttp.web_response.json_response(events_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        events = await system.async_get_events(datetime.now(), 2)
        assert len(events) == 2

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_missing_property(
    aresponses,
    caplog,
    server,
    subscriptions_response,
    v3_sensors_response,
    v3_settings_response,
):
    """Test that missing property data is handled correctly."""
    subscriptions_response["subscriptions"][0]["location"]["system"].pop("isOffline")

    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_USER_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(subscriptions_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    server.add(
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
        assert system.offline is False
        assert any(
            "SimpliSafe didn't return data for property: offline" in e.message
            for e in caplog.records
        )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_missing_system_info(aresponses, caplog, server, subscriptions_response):
    """Test that a subscription with missing system data is handled correctly."""
    subscriptions_response["subscriptions"][0]["location"]["system"] = {}

    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(subscriptions_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        await simplisafe.async_get_systems()
        assert any(
            "Skipping subscription with missing system data" in e.message
            for e in caplog.records
        )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_properties(aresponses, v2_server):
    """Test that base system properties are created properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert not system.alarm_going_off
        assert system.address == TEST_ADDRESS
        assert system.connection_type == "wifi"
        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.state == SystemStates.off
        assert system.system_id == TEST_SYSTEM_ID
        assert system.temperature == 67
        assert system.version == 2

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unknown_sensor_type(aresponses, caplog, v2_server):
    """Test whether a message is logged upon finding an unknown sensor type."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        await simplisafe.async_get_systems()
        assert any("Unknown device type" in e.message for e in caplog.records)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unknown_system_state(
    aresponses,
    caplog,
    server,
    subscriptions_response,
    v3_sensors_response,
    v3_settings_response,
):
    """Test that an unknown system state is logged."""
    subscriptions_response["subscriptions"][0]["location"]["system"][
        "alarmState"
    ] = "NOT_REAL_STATE"

    server.add(
        "api.simplisafe.com",
        f"/v1/users/{TEST_USER_ID}/subscriptions",
        "get",
        response=aiohttp.web_response.json_response(subscriptions_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
        "get",
        response=aiohttp.web_response.json_response(v3_settings_response, status=200),
    )
    server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
        "get",
        response=aiohttp.web_response.json_response(v3_sensors_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        await simplisafe.async_get_systems()
        assert any("Unknown raw system state" in e.message for e in caplog.records)
        assert any("NOT_REAL_STATE" in e.message for e in caplog.records)

    aresponses.assert_plan_strictly_followed()
