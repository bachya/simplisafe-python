"""Define tests for the Lock objects."""
import aiohttp
import pytest

from simplipy import API
from simplipy.errors import InvalidCredentialsError
from simplipy.lock import LockStates

from .common import (
    TEST_EMAIL,
    TEST_LOCK_ID,
    TEST_LOCK_ID_2,
    TEST_LOCK_ID_3,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    load_fixture,
)


@pytest.mark.asyncio
async def test_lock_unlock(aresponses, v3_server):
    """Test locking the lock."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v3_lock_unlock_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v3_lock_lock_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            lock = system.locks[TEST_LOCK_ID]
            assert lock.state == LockStates.locked

            await lock.unlock()
            assert lock.state == LockStates.unlocked

            await lock.lock()
            assert lock.state == LockStates.locked


@pytest.mark.asyncio
async def test_jammed(v3_server):
    """Test that a jammed lock shows the correct state."""
    async with v3_server:
        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            lock = system.locks[TEST_LOCK_ID_2]
            assert lock.state is LockStates.jammed


@pytest.mark.asyncio
async def test_no_state_change_on_failure(aresponses, v3_server):
    """Test that the lock doesn't change state on error."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            aresponses.Response(text=None, status=401),
        )
        v3_server.add(
            "api.simplisafe.com",
            "/v1/api/token",
            "post",
            aresponses.Response(text="", status=401),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            lock = system.locks[TEST_LOCK_ID]
            assert lock.state == LockStates.locked

            with pytest.raises(InvalidCredentialsError):
                await lock.unlock()
            assert lock.state == LockStates.locked


@pytest.mark.asyncio
async def test_properties(v3_server):
    """Test that lock properties are created properly."""
    async with v3_server:
        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
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


@pytest.mark.asyncio
async def test_unknown_state(caplog, v3_server):
    """Test handling a generic error during update."""
    async with v3_server:
        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]
            lock = system.locks[TEST_LOCK_ID_3]

            assert lock.state == LockStates.unknown

            assert any("Unknown raw lock state" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_update(aresponses, v3_server):
    """Test updating the lock."""
    async with v3_server:
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v3_lock_unlock_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v3_lock_lock_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            aresponses.Response(
                text=load_fixture("v3_sensors_response.json"), status=200
            ),
        )
        v3_server.add(
            "api.simplisafe.com",
            f"/v1/doorlock/{TEST_SUBSCRIPTION_ID}/{TEST_LOCK_ID}/state",
            "post",
            aresponses.Response(
                text=load_fixture("v3_lock_lock_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
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
