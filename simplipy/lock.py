"""Define a SimpliSafe lock."""
from enum import Enum
import logging

from .entity import EntityV3

_LOGGER: logging.Logger = logging.getLogger(__name__)


class LockStates(Enum):
    """Define states that the lock can be in."""

    unlocked = 0
    locked = 1
    jammed = 2


SET_STATE_MAP = {LockStates.locked: "lock", LockStates.unlocked: "unlock"}


class Lock(EntityV3):
    """Define a lock."""

    @property
    def disabled(self) -> bool:
        """Return whether the lock is disabled."""
        return self.entity_data["status"]["lockDisabled"]

    @property
    def lock_low_battery(self) -> bool:
        """Return whether the lock's battery is low."""
        return self.entity_data["status"]["lockLowBattery"]

    @property
    def pin_pad_low_battery(self) -> bool:
        """Return whether the pin pad's battery is low."""
        return self.entity_data["status"]["pinPadLowBattery"]

    @property
    def pin_pad_offline(self) -> bool:
        """Return whether the pin pad is offline."""
        return self.entity_data["status"]["pinPadOffline"]

    @property
    def state(self) -> LockStates:
        """Return the current state of the lock."""
        if bool(self.entity_data["status"]["lockJamState"]):
            return LockStates.jammed
        return LockStates(self.entity_data["status"]["lockState"])

    async def _set_lock_state(self, state: LockStates) -> None:
        """Set the lock state."""
        await self._api.request(
            "post",
            f"doorlock/{self._system_id}/{self.serial}/state",
            json={"state": SET_STATE_MAP[state]},
        )

        self.entity_data["status"]["lockState"] = state.value

    async def lock(self) -> None:
        """Lock the lock."""
        await self._set_lock_state(LockStates.locked)

    async def unlock(self) -> None:
        """Unlock the lock."""
        await self._set_lock_state(LockStates.unlocked)
