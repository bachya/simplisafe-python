"""Define a V2 (original) SimpliSafe system."""
from __future__ import annotations

from typing import Any

from simplipy.const import LOGGER
from simplipy.device.sensor.v2 import SensorV2
from simplipy.system import (
    CONF_DURESS_PIN,
    CONF_MASTER_PIN,
    DEFAULT_MAX_USER_PINS,
    System,
    SystemStates,
    get_device_type_from_data,
)


def create_pin_payload(pins: dict[str, Any]) -> dict[str, dict[str, dict[str, str]]]:
    """Create the request payload to send for updating PINs.

    Args:
        pins: A dictionary of pins.

    Returns:
        A SimpliSafe V2 PIN payload.
    """
    duress_pin = pins.pop(CONF_DURESS_PIN)
    master_pin = pins.pop(CONF_MASTER_PIN)

    payload = {
        "pins": {CONF_DURESS_PIN: {"value": duress_pin}, "pin1": {"value": master_pin}}
    }

    empty_user_index = len(pins)
    for idx, (label, pin) in enumerate(pins.items()):
        payload["pins"][f"pin{idx + 2}"] = {"name": label, "value": pin}

    for idx in range(DEFAULT_MAX_USER_PINS - empty_user_index):
        payload["pins"][f"pin{str(idx + 2 + empty_user_index)}"] = {
            "name": "",
            "pin": "",
        }

    LOGGER.debug("PIN payload: %s", payload)

    return payload


class SystemV2(System):
    """Define a V2 (original) system."""

    async def _async_clear_notifications(self) -> None:
        """Clear active notifications."""
        await self._api.async_request(
            "delete", f"subscriptions/{self.system_id}/messages"
        )

    async def _async_set_state(self, value: SystemStates) -> None:
        """Set the state of the system.

        Args:
            value: A :meth:`simplipy.system.SystemStates` object.
        """
        await self._api.async_request(
            "post",
            f"subscriptions/{self.system_id}/state",
            params={"state": value.name.lower()},
        )

        self._state = value

    async def _async_set_updated_pins(self, pins: dict[str, Any]) -> None:
        """Post new PINs.

        Args:
            pins: A dictionary of PINs.
        """
        await self._api.async_request(
            "post",
            f"subscriptions/{self.system_id}/pins",
            json=create_pin_payload(pins),
        )

    async def _async_update_device_data(self, cached: bool = True) -> None:
        """Update all device data.

        Args:
            cached: Whether to update with cached data.
        """
        sensor_resp = await self._api.async_request(
            "get",
            f"subscriptions/{self.system_id}/settings",
            params={"settingsType": "all", "cached": str(cached).lower()},
        )

        for sensor in sensor_resp.get("settings", {}).get("sensors", []):
            if not sensor:
                continue
            self.sensor_data[sensor["serial"]] = sensor

    async def _async_update_settings_data(self, cached: bool = True) -> None:
        """Update all settings data.

        Args:
            cached: Whether to update with cached data.
        """
        pass

    def generate_device_objects(self) -> None:
        """Generate device objects for this system."""
        for serial, data in self.sensor_data.items():
            sensor_type = get_device_type_from_data(data)
            self.sensors[serial] = SensorV2(self, sensor_type, serial)

    async def async_get_pins(self, cached: bool = True) -> dict[str, str]:
        """Return all of the set PINs, including master and duress.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        Args:
            cached: Whether to update with cached data.

        Returns:
            A dictionary of PINs.
        """
        pins_resp = await self._api.async_request(
            "get",
            f"subscriptions/{self.system_id}/pins",
            params={"settingsType": "all", "cached": str(cached).lower()},
        )

        pins = {
            CONF_MASTER_PIN: pins_resp["pins"].pop("pin1")["value"],
            CONF_DURESS_PIN: pins_resp["pins"].pop("duress")["value"],
        }

        for user_pin in [p for p in pins_resp["pins"].values() if p["value"]]:
            pins[user_pin["name"]] = user_pin["value"]

        return pins
