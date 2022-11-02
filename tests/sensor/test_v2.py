"""Define tests for V2 Sensor objects."""
from typing import cast

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.device.sensor.v2 import SensorV2
from simplipy.errors import SimplipyError
from tests.common import TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, TEST_SYSTEM_ID


@pytest.mark.asyncio
async def test_properties_v2(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v2: ResponsesMockServer,
) -> None:
    """Test that v2 sensor properties are created properly."""
    async with authenticated_simplisafe_server_v2, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        keypad: SensorV2 = cast(SensorV2, system.sensors["195"])
        assert keypad.data == 0
        assert not keypad.error
        assert not keypad.low_battery
        assert keypad.settings == 1

        # Ensure that attempting to access the triggered of anything but
        # an entry sensor in a V2 system throws an error:
        with pytest.raises(SimplipyError):
            assert keypad.triggered == 42

        entry_sensor: SensorV2 = cast(SensorV2, system.sensors["609"])
        assert entry_sensor.data == 130
        assert not entry_sensor.error
        assert not entry_sensor.low_battery
        assert entry_sensor.settings == 1
        assert not entry_sensor.trigger_instantly
        assert not entry_sensor.triggered

    aresponses.assert_plan_strictly_followed()
