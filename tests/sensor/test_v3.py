"""Define tests for v3 Sensor objects."""

from typing import cast

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.device.sensor.v3 import SensorV3
from tests.common import TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, TEST_SYSTEM_ID


@pytest.mark.asyncio
async def test_properties_v3(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that v3 sensor properties are created properly."""
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        entry_sensor: SensorV3 = cast(SensorV3, system.sensors["825"])
        assert not entry_sensor.error
        assert not entry_sensor.low_battery
        assert not entry_sensor.offline
        assert not entry_sensor.settings["instantTrigger"]
        assert not entry_sensor.trigger_instantly
        assert not entry_sensor.triggered

        siren: SensorV3 = cast(SensorV3, system.sensors["236"])
        assert not siren.triggered

        temperature_sensor: SensorV3 = cast(SensorV3, system.sensors["320"])
        assert temperature_sensor.temperature == 67

        # Ensure that attempting to access the temperature attribute of a
        # non-temperature sensor throws an error:
        with pytest.raises(AttributeError):
            assert siren.temperature == 42

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_properties_v3_missing_fields_return_defaults(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that V3 properties return safe defaults when API fields are absent.

    Regression test for home-assistant/core#172599.
    """
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        sensor: SensorV3 = cast(SensorV3, system.sensors["825"])

        # Remove optional nested fields to simulate a sparse API response
        system.sensor_data["825"].pop("status", None)
        system.sensor_data["825"].pop("flags", None)
        system.sensor_data["825"].pop("setting", None)

        assert not sensor.error
        assert not sensor.low_battery
        assert not sensor.offline
        assert sensor.settings == {}

    aresponses.assert_plan_strictly_followed()
