"""Define base tests for Sensor objects."""
import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.device import DeviceTypes
from tests.common import TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, TEST_SYSTEM_ID


@pytest.mark.asyncio
async def test_properties_base(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v2: ResponsesMockServer,
) -> None:
    """Test that base sensor properties are created properly."""
    async with authenticated_simplisafe_server_v2, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        sensor = system.sensors["195"]
        assert sensor.name == "Garage Keypad"
        assert sensor.serial == "195"
        assert sensor.type == DeviceTypes.KEYPAD

    aresponses.assert_plan_strictly_followed()
