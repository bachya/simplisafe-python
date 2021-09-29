"""Define base tests for Sensor objects."""
# pylint: disable=unused-argument
import aiohttp
import pytest

from simplipy import API
from simplipy.device import DeviceTypes

from tests.common import TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, TEST_SYSTEM_ID


@pytest.mark.asyncio
async def test_properties_base(aresponses, v2_server):
    """Test that base sensor properties are created properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]
        sensor = system.sensors["195"]
        assert sensor.name == "Garage Keypad"
        assert sensor.serial == "195"
        assert sensor.type == DeviceTypes.keypad

    aresponses.assert_plan_strictly_followed()
