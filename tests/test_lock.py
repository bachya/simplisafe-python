"""Define tests for the Lock objects."""
# pylint: disable=protected-access,unused-argument
from datetime import datetime

import aiohttp
import pytest

from simplipy import API
from simplipy.device.lock import LockStates
from simplipy.errors import InvalidCredentialsError

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
async def test_lock_unlock(aresponses, v3_lock_state_response, v3_server):
    """Test locking and unlocking the lock."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v3_lock_state_response, status=200),
    )

    v3_lock_state_response["state"] = "unlock"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v3_lock_state_response, status=200),
    )

    v3_lock_state_response["state"] = "lock"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v3_lock_state_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        lock = system.locks[TEST_LOCK_ID]
        assert lock.state == LockStates.locked

        await lock.async_unlock()
        assert lock.state == LockStates.unlocked

        await lock.async_lock()
        assert lock.state == LockStates.locked

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_jammed(aresponses, v3_server):
    """Test that a jammed lock shows the correct state."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        lock = system.locks[TEST_LOCK_ID_2]
        assert lock.state is LockStates.jammed

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_no_state_change_on_failure(
    aresponses, invalid_refresh_token_response, v3_server
):
    """Test that the lock doesn't change state on error."""
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
        "post",
        response=aresponses.Response(text="Unauthorized", status=401),
    )
    v3_server.add(
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
        simplisafe._access_token_expire_dt = datetime.utcnow()

        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        lock = system.locks[TEST_LOCK_ID]
        assert lock.state == LockStates.locked

        with pytest.raises(InvalidCredentialsError):
            await lock.async_unlock()
        assert lock.state == LockStates.locked

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_properties(aresponses, v3_server):
    """Test that lock properties are created properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        lock = system.locks[TEST_LOCK_ID]
        assert not lock.disabled
        assert not lock.error
        assert not lock.lock_low_battery
        assert not lock.low_battery
        assert not lock.offline
        assert not lock.pin_pad_low_battery
        assert not lock.pin_pad_offline
        assert lock.state is LockStates.locked

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unknown_state(aresponses, caplog, v3_server):
    """Test handling a generic error during update."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        lock = system.locks[TEST_LOCK_ID_3]
        assert lock.state == LockStates.unknown

        assert any("Unknown raw lock state" in e.message for e in caplog.records)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_update(
    aresponses, v3_lock_state_response, v3_sensors_response, v3_server
):
    """Test updating the lock."""
    v3_lock_state_response["state"] = "unlock"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v3_lock_state_response, status=200),
    )

    v3_lock_state_response["state"] = "lock"

    v3_server.add(
        "api.simplisafe.com",
        f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v3_lock_state_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
        "get",
        response=aiohttp.web_response.json_response(v3_sensors_response, status=200),
    )
    v3_server.add(
        "api.simplisafe.com",
        f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
        "post",
        response=aiohttp.web_response.json_response(v3_lock_state_response, status=200),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        lock = system.locks[TEST_LOCK_ID]
        assert lock.state == LockStates.locked

        await lock.async_unlock()
        assert lock.state == LockStates.unlocked

        # Simulate a manual lock and an update some time later:
        await lock.async_update()
        assert lock.state == LockStates.locked

    aresponses.assert_plan_strictly_followed()
