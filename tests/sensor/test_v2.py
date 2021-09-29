"""Define tests for v2 Sensor objects."""
# pylint: disable=unused-argument
import aiohttp
import pytest

from simplipy import API
from simplipy.errors import SimplipyError

from tests.common import TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, TEST_SYSTEM_ID


@pytest.mark.asyncio
async def test_properties_v2(aresponses, v2_server):
    """Test that v2 sensor properties are created properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]
        keypad = system.sensors["195"]
        assert keypad.data == 0
        assert not keypad.error
        assert not keypad.low_battery
        assert keypad.settings == 1

        # Ensure that attempting to access the triggered of anything but
        # an entry sensor in a V2 system throws an error:
        with pytest.raises(SimplipyError):
            assert keypad.triggered == 42

        entry_sensor = system.sensors["609"]
        assert entry_sensor.data == 130
        assert not entry_sensor.error
        assert not entry_sensor.low_battery
        assert entry_sensor.settings == 1
        assert not entry_sensor.trigger_instantly
        assert not entry_sensor.triggered

    aresponses.assert_plan_strictly_followed()
