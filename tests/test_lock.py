"""Define tests for the Lock objects."""
import aiohttp
import pytest

from simplipy import API
from simplipy.entity import EntityTypes
from simplipy.errors import SimplipyError

from .const import TEST_EMAIL, TEST_PASSWORD, TEST_SYSTEM_ID
from .fixtures import *
from .fixtures.v2 import *
from .fixtures.v3 import *


@pytest.mark.asyncio
async def test_properties(event_loop, v3_server):
    """Test that lock properties are created properly."""
    async with v3_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            api = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD, websession)
            systems = await api.get_systems()
            system = systems[TEST_SYSTEM_ID]

            lock = system.locks["987"]
            assert not lock.disabled
            assert not lock.error
            assert not lock.jammed
            assert not lock.lock_low_battery
            assert lock.locked is True
            assert not lock.low_battery
            assert not lock.offline
            assert not lock.pin_pad_low_battery
            assert not lock.pin_pad_offline
