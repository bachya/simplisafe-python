"""Define tests for v3 Sensor objects."""
# pylint: disable=unused-argument
import aiohttp
import pytest

from simplipy import API

from tests.common import TEST_PASSWORD, TEST_SYSTEM_ID, TEST_USERNAME


@pytest.mark.asyncio
async def test_properties_v3(aresponses, v3_server):
    """Test that v3 sensor properties are created properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_credentials(
            TEST_USERNAME, TEST_PASSWORD, session=session
        )
        await simplisafe.async_verify_2fa_email()

        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]

        entry_sensor = system.sensors["825"]
        assert not entry_sensor.error
        assert not entry_sensor.low_battery
        assert not entry_sensor.offline
        assert not entry_sensor.settings["instantTrigger"]
        assert not entry_sensor.trigger_instantly
        assert not entry_sensor.triggered

        siren = system.sensors["236"]
        assert not siren.triggered

        temperature_sensor = system.sensors["320"]
        assert temperature_sensor.temperature == 67

        # Ensure that attempting to access the temperature attribute of a
        # non-temperature sensor throws an error:
        with pytest.raises(AttributeError):
            assert siren.temperature == 42

    aresponses.assert_plan_strictly_followed()
