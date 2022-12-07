"""Define base tests for System objects."""
from datetime import datetime
from typing import Any, cast
from unittest.mock import Mock

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.system import SystemStates
from simplipy.system.v3 import SystemV3
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
async def test_deactivated_system(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server: ResponsesMockServer,
    subscriptions_response: dict[str, Any],
) -> None:
    """Test that API.async_get_systems doesn't return deactivated systems.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server: A authenticated API connection.
        subscriptions_response: An API response payload.
    """
    subscriptions_response["subscriptions"][0]["status"]["hasBaseStation"] = 0

    async with authenticated_simplisafe_server:
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
            "get",
            response=aiohttp.web_response.json_response(
                subscriptions_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            assert len(systems) == 0

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_get_events(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v2: ResponsesMockServer,
    events_response: dict[str, Any],
) -> None:
    """Test getting events from a system.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v2: A authenticated API connection.
        events_response: An API response payload.
    """
    async with authenticated_simplisafe_server_v2:
        authenticated_simplisafe_server_v2.add(
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
async def test_missing_property(  # pylint: disable=too-many-arguments
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server: ResponsesMockServer,
    caplog: Mock,
    subscriptions_response: dict[str, Any],
    v3_sensors_response: dict[str, Any],
    v3_settings_response: dict[str, Any],
) -> None:
    """Test that missing property data is handled correctly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server: A authenticated API connection.
        caplog: A mocked logging utility.
        subscriptions_response: An API response payload.
        v3_sensors_response: An API response payload.
        v3_settings_response: An API response payload.
    """
    subscriptions_response["subscriptions"][0]["location"]["system"].pop("isOffline")

    async with authenticated_simplisafe_server:
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            response=aiohttp.web_response.json_response(
                subscriptions_response, status=200
            ),
        )
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            response=aiohttp.web_response.json_response(
                v3_sensors_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
            assert system.offline is False
            assert any(
                "SimpliSafe didn't return data for property: offline" in e.message
                for e in caplog.records
            )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_missing_system_info(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server: ResponsesMockServer,
    caplog: Mock,
    subscriptions_response: dict[str, Any],
) -> None:
    """Test that a subscription with missing system data is handled correctly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server: A authenticated API connection.
        caplog: A mocked logging utility.
        subscriptions_response: An API response payload.
    """
    subscriptions_response["subscriptions"][0]["location"]["system"] = {}

    async with authenticated_simplisafe_server:
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_SUBSCRIPTION_ID}/subscriptions",
            "get",
            response=aiohttp.web_response.json_response(
                subscriptions_response, status=200
            ),
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
async def test_properties(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v2: ResponsesMockServer,
) -> None:
    """Test that base system properties are created properly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v2: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v2, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert not system.alarm_going_off
        assert system.address == TEST_ADDRESS
        assert system.connection_type == "wifi"
        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.state == SystemStates.OFF
        assert system.system_id == TEST_SYSTEM_ID
        assert system.temperature == 67
        assert system.version == 2

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unknown_sensor_type(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v2: ResponsesMockServer,
    caplog: Mock,
) -> None:
    """Test whether a message is logged upon finding an unknown sensor type.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v2: A authenticated API connection.
        caplog: A mocked logging utility.
    """
    async with authenticated_simplisafe_server_v2, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        await simplisafe.async_get_systems()
        assert any("Unknown device type" in e.message for e in caplog.records)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unknown_system_state(  # pylint: disable=too-many-arguments
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server: ResponsesMockServer,
    caplog: Mock,
    subscriptions_response: dict[str, Any],
    v3_sensors_response: dict[str, Any],
    v3_settings_response: dict[str, Any],
) -> None:
    """Test that an unknown system state is logged.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server: A authenticated API connection.
        caplog: A mocked logging utility.
        subscriptions_response: An API response payload.
        v3_sensors_response: An API response payload.
        v3_settings_response: An API response payload.
    """
    subscriptions_response["subscriptions"][0]["location"]["system"][
        "alarmState"
    ] = "NOT_REAL_STATE"

    async with authenticated_simplisafe_server:
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            response=aiohttp.web_response.json_response(
                subscriptions_response, status=200
            ),
        )
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            response=aiohttp.web_response.json_response(
                v3_sensors_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            await simplisafe.async_get_systems()
            assert any("Unknown raw system state" in e.message for e in caplog.records)
            assert any("NOT_REAL_STATE" in e.message for e in caplog.records)

    aresponses.assert_plan_strictly_followed()
