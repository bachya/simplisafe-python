"""Define a V2 (original) SimpliSafe system."""
from enum import Enum
import logging
from typing import Dict

from simplipy.system import (
    CONF_DURESS_PIN,
    CONF_MASTER_PIN,
    System,
    SystemStates,
    create_pin_payload,
)

_LOGGER: logging.Logger = logging.getLogger(__name__)


class SystemV2(System):
    """Define a V2 (original) system."""

    async def _get_entities_payload(self, cached: bool = True) -> dict:
        """Update sensors to the latest values."""
        sensor_resp = await self._request(
            "get",
            f"subscriptions/{self.system_id}/settings",
            params={"settingsType": "all", "cached": str(cached).lower()},
        )

        return sensor_resp["settings"]["sensors"]

    async def _send_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        await self._request(
            "post",
            f"subscriptions/{self.system_id}/pins",
            json=create_pin_payload(pins, version=2),
        )

    async def _set_state(self, value: Enum) -> None:
        """Set the state of the system."""
        state_resp: dict = await self._request(
            "post",
            f"subscriptions/{self.system_id}/state",
            params={"state": value.name},
        )

        _LOGGER.debug('Set "%s" response: %s', value.name, state_resp)

        if not state_resp:
            return

        if state_resp["success"]:
            self._state = SystemStates[state_resp["requestedState"]]

    async def get_pins(self, cached: bool = True) -> Dict[str, str]:
        """Return all of the set PINs, including master and duress."""
        pins_resp: dict = await self._request(
            "get",
            f"subscriptions/{self.system_id}/pins",
            params={"settingsType": "all", "cached": str(cached).lower()},
        )

        pins: Dict[str, str] = {
            CONF_MASTER_PIN: pins_resp["pins"].pop("pin1")["value"],
            CONF_DURESS_PIN: pins_resp["pins"].pop("duress")["value"],
        }

        user_pin: dict
        for user_pin in [p for p in pins_resp["pins"].values() if p["value"]]:
            pins[user_pin["name"]] = user_pin["value"]

        return pins
