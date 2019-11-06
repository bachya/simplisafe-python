"""Define a SimpliSafe lock."""
import logging

from .entity import EntityV3

_LOGGER: logging.Logger = logging.getLogger(__name__)


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
    def jammed(self) -> bool:
        """Return whether the lock is jammed."""
        return bool(self.entity_data["status"]["lockJamState"])

    @property
    def locked(self) -> bool:
        """Return whether the lock is locked."""
        return bool(self.entity_data["status"]["lockState"])

    @property
    def pin_pad_low_battery(self) -> bool:
        """Return whether the pin pad's battery is low."""
        return self.entity_data["status"]["pinPadLowBattery"]

    @property
    def pin_pad_offline(self) -> bool:
        """Return whether the pin pad is offline."""
        return self.entity_data["status"]["pinPadOffline"]
