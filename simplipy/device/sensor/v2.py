"""Define a v2 (old) SimpliSafe sensor."""
from typing import cast

from simplipy.device import Device, DeviceTypes
from simplipy.errors import SimplipyError


class SensorV2(Device):
    """A V2 (old) sensor.

    Note that this class shouldn't be instantiated directly; it will be
    instantiated as appropriate via :meth:`simplipy.API.async_get_systems`.
    """

    @property
    def data(self) -> int:
        """Return the sensor's current data flag (currently not understood).

        Returns:
            The current data flag.
        """
        return cast(int, self._system.sensor_data[self._serial]["sensorData"])

    @property
    def error(self) -> bool:
        """Return the sensor's error status.

        Returns:
            The current error status.
        """
        return cast(bool, self._system.sensor_data[self._serial]["error"])

    @property
    def low_battery(self) -> bool:
        """Return whether the sensor's battery is low.

        Returns:
            The current low battery status.
        """
        return cast(
            bool, self._system.sensor_data[self._serial].get("battery", "ok") != "ok"
        )

    @property
    def settings(self) -> bool:
        """Return the sensor's settings.

        Returns:
            The current settings.
        """
        return cast(bool, self._system.sensor_data[self._serial]["setting"])

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly.

        Returns:
            The "instant trigger" settings.
        """
        return cast(bool, self._system.sensor_data[self._serial]["instant"])

    @property
    def triggered(self) -> bool:
        """Return whether the sensor has been triggered.

        Returns:
            The triggered status.

        Raises:
            SimplipyError: Raised when the state can't be determined.
        """
        if self.type == DeviceTypes.ENTRY:
            return cast(
                bool,
                self._system.sensor_data[self._serial].get("entryStatus", "closed")
                == "open",
            )

        raise SimplipyError(f"Cannot determine triggered state for sensor: {self.name}")
