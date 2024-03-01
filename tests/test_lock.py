"""Define tests for the Lock objects."""

# pylint: disable=protected-access
from __future__ import annotations

from datetime import timedelta
from typing import Any, cast
from unittest.mock import Mock

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.device.lock import LockStates
from simplipy.errors import InvalidCredentialsError
from simplipy.system.v3 import SystemV3
from simplipy.util.dt import utcnow

from .common import (
    TEST_AUTHORIZATION_CODE,
    TEST_CODE_VERIFIER,
    TEST_LOCK_ID,
    TEST_LOCK_ID_2,
    TEST_LOCK_ID_3,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
)


@pytest.mark.asyncio
async def test_lock_unlock(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test locking and unlocking the lock.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            response=aresponses.Response(text=None, status=200),
        )

        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            response=aresponses.Response(text=None, status=200),
        )

        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            response=aresponses.Response(text=None, status=200),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
            lock = system.locks[TEST_LOCK_ID]

            state = lock.state
            assert state == LockStates.LOCKED
            await lock.async_unlock()
            state = lock.state
            assert state == LockStates.UNLOCKED
            await lock.async_lock()
            state = lock.state
            assert state == LockStates.LOCKED

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_jammed(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that a jammed lock shows the correct state.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        lock = system.locks[TEST_LOCK_ID_2]
        assert lock.state is LockStates.JAMMED

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_no_state_change_on_failure(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    invalid_refresh_token_response: dict[str, Any],
) -> None:
    """Test that the lock doesn't change state on error.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
        invalid_refresh_token_response: An API response payload.
    """
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            response=aresponses.Response(text="Unauthorized", status=401),
        )
        authenticated_simplisafe_server_v3.add(
            "auth.simplisafe.com",
            "/oauth/token",
            "post",
            response=aiohttp.web_response.json_response(
                invalid_refresh_token_response, status=401
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE,
                TEST_CODE_VERIFIER,
                session=session,
            )

            # Manually set the expiration datetime to force a refresh token flow:
            simplisafe._token_last_refreshed = utcnow() - timedelta(seconds=30)

            systems = await simplisafe.async_get_systems()
            system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
            lock = system.locks[TEST_LOCK_ID]
            assert lock.state == LockStates.LOCKED

            with pytest.raises(InvalidCredentialsError):
                await lock.async_unlock()
            assert lock.state == LockStates.LOCKED

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_properties(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that lock properties are created properly.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        lock = system.locks[TEST_LOCK_ID]
        assert not lock.disabled
        assert not lock.error
        assert not lock.lock_low_battery
        assert not lock.low_battery
        assert not lock.offline
        assert not lock.pin_pad_low_battery
        assert not lock.pin_pad_offline
        assert lock.state is LockStates.LOCKED

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unknown_state(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    caplog: Mock,
) -> None:
    """Test handling a generic error during update.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
        caplog: A mocked logging utility.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
        lock = system.locks[TEST_LOCK_ID_3]
        assert lock.state == LockStates.UNKNOWN

        assert any("Unknown raw lock state" in e.message for e in caplog.records)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_update(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_sensors_response: dict[str, Any],
) -> None:
    """Test updating the lock.

    Args:
        aresponses: An aresponses server.
        authenticated_simplisafe_server_v3: A authenticated API connection.
        v3_sensors_response: An API response payload.
    """
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            response=aresponses.Response(text=None, status=200),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            response=aresponses.Response(text=None, status=200),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            response=aiohttp.web_response.json_response(
                v3_sensors_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            response=aresponses.Response(text=None, status=200),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
            lock = system.locks[TEST_LOCK_ID]

            state = lock.state
            assert state == LockStates.LOCKED
            await lock.async_unlock()
            state = lock.state
            assert state == LockStates.UNLOCKED
            await lock.async_update()
            state = lock.state
            assert state == LockStates.LOCKED

    aresponses.assert_plan_strictly_followed()
