"""Define a V2 (original) SimpliSafe system."""
from typing import Dict

from simplipy.sensor.v2 import SensorV2
from simplipy.system import (
    CONF_DURESS_PIN,
    CONF_MASTER_PIN,
    DEFAULT_MAX_USER_PINS,
    System,
    SystemStates,
    get_entity_type_from_data,
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

    return payload


class SystemV2(System):
    """Define a V2 (original) system."""

    async def _update_entity_data(self, cached: bool = True) -> None:
        """Update sensors to the latest values."""
        sensor_resp = await self._api.request(
            "get",
            f"subscriptions/{self.system_id}/settings",
            params={"settingsType": "all", "cached": str(cached).lower()},
        )

        for entity in sensor_resp.get("settings", {}).get("sensors", []):
            if not entity:
                continue
            self.entity_data[entity["serial"]] = entity

    async def _set_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        await self._api.request(
            "post",
            f"subscriptions/{self.system_id}/pins",
            json=create_pin_payload(pins),
        )

    async def _set_state(self, value: SystemStates) -> None:
        """Set the state of the system."""
        state_resp = await self._api.request(
            "post",
            f"subscriptions/{self.system_id}/state",
            params={"state": value.name},
        )

        if state_resp["success"]:
            self._state = SystemStates[state_resp["requestedState"]]

    async def generate_entities(self) -> None:
        """Generate entity objects for this system."""
        for serial, entity in self.entity_data.items():
            entity_type = get_entity_type_from_data(entity)
            self.sensors[serial] = SensorV2(self._api, self, entity_type, serial)

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
