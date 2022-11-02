"""Define a base SimpliSafe device."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from simplipy.system import System


class DeviceTypes(Enum):
    """Device types based on internal SimpliSafe ID number."""

    REMOTE = 0
    KEYPAD = 1
    KEYCHAIN = 2
    PANIC_BUTTON = 3
    MOTION = 4
    ENTRY = 5
    GLASS_BREAK = 6
    CARBON_MONOXIDE = 7
    SMOKE = 8
    LEAK = 9
    TEMPERATURE = 10
    CAMERA = 12
    SIREN = 13
    DOORBELL = 15
    LOCK = 16
    OUTDOOR_CAMERA = 17
    LOCK_KEYPAD = 253
    UNKNOWN = 99


class Device:
    """A base SimpliSafe device.

    Note that this class shouldn't be instantiated directly; it will be instantiated as
    appropriate via :meth:`simplipy.API.async_get_systems`.

    Args:
        system: A :meth:`simplipy.system.System` object (or one of its subclasses).
        device_type: The type of device represented.
        serial: The serial number of the device.
    """

    def __init__(self, system: System, device_type: DeviceTypes, serial: str) -> None:
        """Initialize.

        Args:
            system: A :meth:`simplipy.system.System` object (or one of its subclasses).
            device_type: The type of device represented.
            serial: The serial number of the device.
        """
        self._device_type = device_type
        self._serial = serial
        self._system = system

    @property
    def name(self) -> str:
        """Return the device name.

        Returns:
            The device name.
        """
        return cast(str, self._system.sensor_data[self._serial]["name"])

    @property
    def serial(self) -> str:
        """Return the device's serial number.

        Returns:
            The device serial number.
        """
        return cast(str, self._system.sensor_data[self._serial]["serial"])

    @property
    def type(self) -> DeviceTypes:
        """Return the device type.

        Returns:
            The device type.
        """
        return self._device_type

    def as_dict(self) -> dict[str, Any]:
        """Return dictionary version of this device.

        Returns:
            Returns a dict representation of this device.
        """
        return {
            "name": self.name,
            "serial": self.serial,
            "type": self.type.value,
        }

    async def async_update(self, cached: bool = True) -> None:
        """Retrieve the latest state/properties for the device.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        Args:
            cached: Whether to used cached data.
        """
        await self._system.async_update(
            include_subscription=False, include_settings=False, cached=cached
        )


class DeviceV3(Device):
    """A base device for V3 systems.

    Note that this class shouldn't be instantiated directly; it will be
    instantiated as appropriate via :meth:`simplipy.API.async_get_systems`.
    """

    @property
    def error(self) -> bool:
        """Return the device's error status.

        Returns:
            The device's error status.
        """
        return cast(
            bool,
            self._system.sensor_data[self._serial]["status"].get("malfunction", False),
        )

    @property
    def low_battery(self) -> bool:
        """Return whether the device's battery is low.

        Returns:
            The device's low battery status.
        """
        return cast(bool, self._system.sensor_data[self._serial]["flags"]["lowBattery"])

    @property
    def offline(self) -> bool:
        """Return whether the device is offline.

        Returns:
            The device's offline status.
        """
        return cast(bool, self._system.sensor_data[self._serial]["flags"]["offline"])

    @property
    def settings(self) -> dict[str, Any]:
        """Return the device's settings.

        Note that these can change based on what device type the device is.

        Returns:
            A settings dictionary.
        """
        return cast(dict[str, Any], self._system.sensor_data[self._serial]["setting"])

    def as_dict(self) -> dict[str, Any]:
        """Return dictionary version of this device.

        Returns:
            A dict representation of this device.
        """
        return {
            **super().as_dict(),
            "error": self.error,
            "low_battery": self.low_battery,
            "offline": self.offline,
            "settings": self.settings,
        }
