"""Define a SimpliSafe lock."""
from enum import Enum
from typing import TYPE_CHECKING, Awaitable, Callable, cast

from simplipy.const import LOGGER
from simplipy.device import DeviceTypes, DeviceV3

if TYPE_CHECKING:
    from simplipy.system import System


class LockStates(Enum):
    """States that a lock can be in."""

    UNLOCKED = 0
    LOCKED = 1
    JAMMED = 2
    UNKNOWN = 99


class Lock(DeviceV3):
    """A lock that works with V3 systems.

    Note that this class shouldn't be instantiated directly; it will be
    instantiated as appropriate via :meth:`simplipy.API.async_get_systems`.

    :param api: A :meth:`simplipy.API` object
    :type api: :meth:`simplipy.API`
    :param system: A :meth:`simplipy.system.System` object (or one of its subclasses)
    :type system: :meth:`simplipy.system.System`
    :param device_type: The type of device represented
    :type device_type: :meth:`simplipy.device.DeviceTypes`
    :param serial: The serial number of the device
    :type serial: ``str``
    """

    class _InternalStates(Enum):
        """Define an enum to map internal lock states to values we understand."""

        LOCKED = 1
        UNLOCKED = 2

    def __init__(
        self,
        request: Callable[..., Awaitable],
        system: "System",
        device_type: DeviceTypes,
        serial: str,
    ) -> None:
        """Initialize."""
        super().__init__(system, device_type, serial)

        self._request = request

    @property
    def disabled(self) -> bool:
        """Return whether the lock is disabled.

        :rtype: ``bool``
        """
        return cast(
            bool, self._system.sensor_data[self._serial]["status"]["lockDisabled"]
        )

    @property
    def lock_low_battery(self) -> bool:
        """Return whether the lock's battery is low.

        :rtype: ``bool``
        """
        return cast(
            bool, self._system.sensor_data[self._serial]["status"]["lockLowBattery"]
        )

    @property
    def pin_pad_low_battery(self) -> bool:
        """Return whether the pin pad's battery is low.

        :rtype: ``bool``
        """
        return cast(
            bool, self._system.sensor_data[self._serial]["status"]["pinPadLowBattery"]
        )

    @property
    def pin_pad_offline(self) -> bool:
        """Return whether the pin pad is offline.

        :rtype: ``bool``
        """
        return cast(
            bool, self._system.sensor_data[self._serial]["status"]["pinPadOffline"]
        )

    @property
    def state(self) -> LockStates:
        """Return the current state of the lock.

        :rtype: :meth:`simplipy.lock.LockStates`
        """
        if bool(self._system.sensor_data[self._serial]["status"]["lockJamState"]):
            return LockStates.JAMMED

        raw_state = self._system.sensor_data[self._serial]["status"]["lockState"]

        try:
            internal_state = self._InternalStates(raw_state)
        except ValueError:
            LOGGER.error("Unknown raw lock state: %s", raw_state)
            return LockStates.UNKNOWN

        if internal_state == self._InternalStates.LOCKED:
            return LockStates.LOCKED
        return LockStates.UNLOCKED

    async def async_lock(self) -> None:
        """Lock the lock."""
        await self._request(
            "post",
            f"doorlock/{self._system.system_id}/{self.serial}/state",
            json={"state": "lock"},
        )

        # Update the internal state representation:
        self._system.sensor_data[self._serial]["status"][
            "lockState"
        ] = self._InternalStates.LOCKED.value

    async def async_unlock(self) -> None:
        """Unlock the lock."""
        await self._request(
            "post",
            f"doorlock/{self._system.system_id}/{self.serial}/state",
            json={"state": "unlock"},
        )

        # Update the internal state representation:
        self._system.sensor_data[self._serial]["status"][
            "lockState"
        ] = self._InternalStates.UNLOCKED.value
