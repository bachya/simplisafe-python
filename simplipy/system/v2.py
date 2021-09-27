"""Define a V2 (original) SimpliSafe system."""
from typing import Dict

from simplipy.const import LOGGER
from simplipy.device.sensor.v2 import SensorV2
from simplipy.system import (
    CONF_DURESS_PIN,
    CONF_MASTER_PIN,
    DEFAULT_MAX_USER_PINS,
    System,
    SystemStates,
    coerce_state_from_raw_value,
    get_device_type_from_data,
)


def create_pin_payload(pins: dict) -> Dict[str, Dict[str, Dict[str, str]]]:
    """Create the request payload to send for updating PINs."""
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

    async def _set_state(self, value: SystemStates) -> None:
        """Set the state of the system."""
        state_resp = await self._api.request(
            "post",
            f"subscriptions/{self.system_id}/state",
            params={"state": value.name},
        )

        if state_resp["success"]:
            self._state = coerce_state_from_raw_value(state_resp["requestedState"])

    async def _set_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        await self._api.request(
            "post",
            f"subscriptions/{self.system_id}/pins",
            json=create_pin_payload(pins),
        )

    async def _update_device_data(self, cached: bool = True) -> None:
        """Update sensors to the latest values."""
        sensor_resp = await self._api.request(
            "get",
            f"subscriptions/{self.system_id}/settings",
            params={"settingsType": "all", "cached": str(cached).lower()},
        )

        for sensor in sensor_resp.get("settings", {}).get("sensors", []):
            if not sensor:
                continue
            self.sensor_data[sensor["serial"]] = sensor

    async def _update_settings_data(self, cached: bool = True) -> None:
        """Update all settings data."""
        pass

    def generate_device_objects(self) -> None:
        """Generate device objects for this system."""
        for serial, data in self.sensor_data.items():
            sensor_type = get_device_type_from_data(data)
            self.sensors[serial] = SensorV2(self, sensor_type, serial)

    async def get_pins(self, cached: bool = True) -> Dict[str, str]:
        """Return all of the set PINs, including master and duress.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param cached: Whether to used cached data.
        :type cached: ``bool``
        :rtype: ``Dict[str, str]``
        """
        pins_resp = await self._api.request(
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
