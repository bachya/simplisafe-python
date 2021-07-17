"""Define tests for the Lock objects."""
# pylint: disable=unused-argument
import aiohttp
import pytest

from simplipy import get_api
from simplipy.errors import InvalidCredentialsError
from simplipy.lock import LockStates

from .common import (
    TEST_CLIENT_ID,
    TEST_EMAIL,
    TEST_LOCK_ID,
    TEST_LOCK_ID_2,
    TEST_LOCK_ID_3,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    load_fixture,
)


async def test_lock_unlock(v3_server):
    """Test locking the lock."""
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/doorlock/{TEST_SUBSCRIPTION_ID}/"
            f"{TEST_LOCK_ID}/state"
        ),
        status=200,
        body=load_fixture("v3_lock_unlock_response.json"),
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/doorlock/{TEST_SUBSCRIPTION_ID}/"
            f"{TEST_LOCK_ID}/state"
        ),
        status=200,
        body=load_fixture("v3_lock_lock_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        lock = system.locks[TEST_LOCK_ID]
        assert lock.state == LockStates.locked

        await lock.unlock()
        assert lock.state == LockStates.unlocked

        await lock.lock()
        assert lock.state == LockStates.locked


async def test_jammed(v3_server):
    """Test that a jammed lock shows the correct state."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        lock = system.locks[TEST_LOCK_ID_2]
        assert lock.state is LockStates.jammed


async def test_no_state_change_on_failure(v3_server):
    """Test that the lock doesn't change state on error."""
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/doorlock/{TEST_SUBSCRIPTION_ID}"
            f"/{TEST_LOCK_ID}/state"
        ),
        status=401,
        body="Unauthorized",
    )
    v3_server.post(
        "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
    )
    v3_server.post(
        "https://api.simplisafe.com/v1/api/token", status=401, body="Unauthorized"
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        lock = system.locks[TEST_LOCK_ID]
        assert lock.state == LockStates.locked

        with pytest.raises(InvalidCredentialsError):
            await lock.unlock()
        assert lock.state == LockStates.locked


async def test_properties(v3_server):
    """Test that lock properties are created properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
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


async def test_unknown_state(caplog, v3_server):
    """Test handling a generic error during update."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]
        lock = system.locks[TEST_LOCK_ID_3]

        assert lock.state == LockStates.unknown

        assert any("Unknown raw lock state" in e.message for e in caplog.records)


async def test_update(v3_server):
    """Test updating the lock."""
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/doorlock/{TEST_SUBSCRIPTION_ID}/"
            f"{TEST_LOCK_ID}/state"
        ),
        status=200,
        body=load_fixture("v3_lock_unlock_response.json"),
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/doorlock/{TEST_SUBSCRIPTION_ID}/"
            f"{TEST_LOCK_ID}/state"
        ),
        status=200,
        body=load_fixture("v3_lock_lock_response.json"),
    )
    v3_server.get(
        (
            f"https://api.simplisafe.com/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/"
            f"sensors?forceUpdate=false"
        ),
        status=200,
        body=load_fixture("v3_sensors_response.json"),
    )
    v3_server.post(
        (
            f"https://api.simplisafe.com/v1/doorlock/{TEST_SUBSCRIPTION_ID}/"
            f"{TEST_LOCK_ID}/state"
        ),
        status=200,
        body=load_fixture("v3_lock_lock_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        lock = system.locks[TEST_LOCK_ID]
        assert lock.state == LockStates.locked

        await lock.unlock()
        assert lock.state == LockStates.unlocked

        # Simulate a manual lock and an update some time later:
        await lock.update()
        assert lock.state == LockStates.locked
