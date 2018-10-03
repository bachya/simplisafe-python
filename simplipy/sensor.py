"""Define a SimpliSafe sensor."""
import logging
from enum import Enum
from typing import Union

from .errors import SimplipyError

_LOGGER = logging.getLogger(__name__)


class SensorTypes(Enum):
    """Define sensor types."""

    keypad = 1
    keychain = 2
    panic_button = 3
    motion = 4
    entry = 5
    glass_break = 6
    carbon_monoxide = 7
    smoke = 8
    leak = 9
    temperature = 10
    siren = 13
    unknown = 99


class Sensor:
    """Define a base SimpliSafe sensor."""

    def __init__(self, sensor_data: dict) -> None:
        """Initialize."""
        self.sensor_data = sensor_data

        try:
            self._type = SensorTypes(sensor_data['type'])
        except ValueError:
            _LOGGER.error('Unknown sensor type: %s', self.sensor_data['type'])
            self._type = SensorTypes.unknown

    @property
    def name(self) -> str:
        """Return the sensor name."""
        return self.sensor_data['name']

    @property
    def serial(self) -> str:
        """Return the serial number."""
        return self.sensor_data['serial']

    @property
    def type(self) -> SensorTypes:
        """Return the sensor type."""
        return self._type


class SensorV2(Sensor):
    """Define a V2 (old) sensor."""

    @property
    def data(self) -> int:
        """Return the sensor's current data."""
        return self.sensor_data['sensorData']

    @property
    def error(self) -> bool:
        """Return the sensor's error status."""
        return self.sensor_data['error']

    @property
    def low_battery(self) -> bool:
        """Return whether the sensor's battery is low."""
        return self.sensor_data.get('battery', 'ok') != 'ok'

    @property
    def settings(self) -> bool:
        """Return the sensor's settings."""
        return self.sensor_data['setting']

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly."""
        return self.sensor_data['instant']

    @property
    def triggered(self) -> bool:
        """Return the current sensor state."""
        if self.type == SensorTypes.entry:
            return self.sensor_data.get('entryStatus', 'closed') == 'open'

        raise SimplipyError(
            'Cannot determine triggered state for sensor: {0}'.format(
                self.name))


class SensorV3(Sensor):
    """Define a V3 (new) sensor."""

    @property
    def error(self) -> bool:
        """Return the sensor's error status."""
        return self.sensor_data['status'].get('malfunction', False)

    @property
    def low_battery(self) -> bool:
        """Return whether the sensor's battery is low."""
        return self.sensor_data['flags']['lowBattery']

    @property
    def offline(self) -> bool:
        """Return whether the sensor is offline."""
        return self.sensor_data['flags']['offline']

    @property
    def settings(self) -> dict:
        """Return the sensor's settings."""
        return self.sensor_data['setting']

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly."""
        return self.sensor_data['setting']['instantTrigger']

    @property
    def triggered(self) -> bool:
        """Return the sensor's status info."""
        if self.type in (SensorTypes.motion, SensorTypes.entry,
                         SensorTypes.glass_break, SensorTypes.carbon_monoxide,
                         SensorTypes.smoke, SensorTypes.leak,
                         SensorTypes.temperature):
            return self.sensor_data['status'].get('triggered', False)

        return False

    @property
    def temperature(self) -> Union[None, int]:
        """Return the sensor's status info."""
        if self.type != SensorTypes.temperature:
            raise AttributeError(
                'Non-temperature sensor cannot have a temperature')

        return self.sensor_data['status']['temperature']
