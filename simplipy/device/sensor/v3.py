"""Define a v3 (new) SimpliSafe sensor."""
from __future__ import annotations

from typing import Any, cast

from simplipy.device import DeviceTypes, DeviceV3


class SensorV3(DeviceV3):
    """A V3 (new) sensor.

    Note that this class shouldn't be instantiated directly; it will be
    instantiated as appropriate via :meth:`simplipy.API.async_get_systems`.
    """

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly.

        Returns:
            The "instant trigger" status.
        """
        return cast(
            bool,
            self._system.sensor_data[self._serial]["setting"].get(
                "instantTrigger", False
            ),
        )

    @property
    def triggered(self) -> bool:
        """Return whether the sensor has been triggered.

        Returns:
            The triggered status.
        """
        if self.type in (
            DeviceTypes.CARBON_MONOXIDE,
            DeviceTypes.ENTRY,
            DeviceTypes.GLASS_BREAK,
            DeviceTypes.LEAK,
            DeviceTypes.MOTION,
            DeviceTypes.SMOKE,
            DeviceTypes.TEMPERATURE,
        ):
            return cast(
                bool,
                self._system.sensor_data[self._serial]["status"].get(
                    "triggered", False
                ),
            )

        return False

    @property
    def temperature(self) -> int:
        """Return the temperature of the sensor (as appropriate).

        If the sensor isn't a temperature sensor, an ``AttributeError`` will be raised.

        Returns:
            The temperature.

        Raises:
            AttributeError: Raised when property is read on a non-temperature device.
        """
        if self.type != DeviceTypes.TEMPERATURE:
            raise AttributeError("Non-temperature sensor cannot have a temperature")

        return cast(
            int, self._system.sensor_data[self._serial]["status"]["temperature"]
        )

    def as_dict(self) -> dict[str, Any]:
        """Return dictionary version of this device.

        Returns:
            A dict representation of this device.
        """
        data: dict[str, Any] = {
            **super().as_dict(),
            "trigger_instantly": self.trigger_instantly,
            "triggered": self.triggered,
        }

        if self.type == DeviceTypes.TEMPERATURE:
            data["temperature"] = self.temperature

        return data
