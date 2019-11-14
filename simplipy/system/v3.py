"""Define a V3 (new) SimpliSafe system."""
from enum import Enum
import logging
from typing import Dict

from simplipy.system import CONF_DURESS_PIN, CONF_MASTER_PIN, System, create_pin_payload

_LOGGER: logging.Logger = logging.getLogger(__name__)


class SystemV3(System):
    """Define a V3 (new) system."""

    def __init__(self, api, location_info: dict) -> None:
        """Initialize."""
        super().__init__(api, location_info)

        self._settings_info: dict = {}

    @property
    def alarm_duration(self) -> int:
        """Return the number of seconds an activated alarm will sound for."""
        return self._settings_info["settings"]["normal"]["alarmDuration"]

    @property
    def alarm_volume(self) -> int:
        """Return the loudness of the alarm volume."""
        return self._settings_info["settings"]["normal"]["alarmVolume"]

    @property
    def battery_backup_power_level(self) -> int:
        """Return the power rating of the battery backup."""
        return self._settings_info["basestationStatus"]["backupBattery"]

    @property
    def entry_delay_away(self) -> int:
        """Return the number of seconds to delay when returning to an "away" alarm."""
        return self._settings_info["settings"]["normal"]["entryDelayAway"]

    @property
    def entry_delay_home(self) -> int:
        """Return the number of seconds to delay when returning to an "home" alarm."""
        return self._settings_info["settings"]["normal"]["entryDelayHome"]

    @property
    def exit_delay_away(self) -> int:
        """Return the number of seconds to delay when exiting an "away" alarm."""
        return self._settings_info["settings"]["normal"]["exitDelayAway"]

    @property
    def exit_delay_home(self) -> int:
        """Return the number of seconds to delay when exiting an "home" alarm."""
        return self._settings_info["settings"]["normal"]["exitDelayHome"]

    @property
    def gsm_strength(self) -> int:
        """Return the signal strength of the cell antenna."""
        return self._settings_info["basestationStatus"]["gsmRssi"]

    @property
    def light(self) -> bool:
        """Return whether the base station light is on."""
        return self._settings_info["settings"]["normal"]["light"]

    @property
    def offline(self) -> bool:
        """Return whether the system is offline."""
        return self._location_info["system"]["isOffline"]

    @property
    def power_outage(self) -> bool:
        """Return whether the system is experiencing a power outage."""
        return self._location_info["system"]["powerOutage"]

    @property
    def rf_jamming(self) -> bool:
        """Return whether the base station is noticing RF jamming."""
        return self._settings_info["basestationStatus"]["rfJamming"]

    @property
    def voice_prompt_volume(self) -> int:
        """Return the loudness of the voice prompt."""
        return self._settings_info["settings"]["normal"]["voicePrompts"]

    @property
    def wall_power_level(self) -> int:
        """Return the power rating of the A/C outlet."""
        return self._settings_info["basestationStatus"]["wallPower"]

    @property
    def wifi_ssid(self) -> str:
        """Return the ssid of the base station."""
        return self._settings_info["settings"]["normal"]["wifiSSID"]

    @property
    def wifi_strength(self) -> int:
        """Return the signal strength of the wifi antenna."""
        return self._settings_info["basestationStatus"]["wifiRssi"]

    async def _get_entities_payload(self, cached: bool = True) -> dict:
        """Update sensors to the latest values."""
        sensor_resp = await self.api.request(
            "get",
            f"ss3/subscriptions/{self.system_id}/sensors",
            params={"forceUpdate": str(not cached).lower()},
        )

        return sensor_resp["sensors"]

    async def _send_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        self._settings_info = await self.api.request(
            "post",
            f"ss3/subscriptions/{self.system_id}/settings/pins",
            json=create_pin_payload(pins),
        )

    async def _set_state(self, value: Enum) -> None:
        """Set the state of the system."""
        state_resp: dict = await self.api.request(
            "post", f"ss3/subscriptions/{self.system_id}/state/{value.name}"
        )

        _LOGGER.debug('Set "%s" response: %s', value.name, state_resp)

        if not state_resp:
            return

        self._state = self._coerce_state_from_string(state_resp["state"])

    async def _update_settings(self, cached: bool = True) -> None:
        """Update system settings."""
        settings_resp: dict = await self.api.request(
            "get",
            f"ss3/subscriptions/{self.system_id}/settings/pins",
            params={"forceUpdate": str(not cached).lower()},
        )

        if settings_resp:
            self._settings_info = settings_resp

    async def get_pins(self, cached: bool = True) -> Dict[str, str]:
        """Return all of the set PINs, including master and duress."""
        await self._update_settings(cached)

        pins: Dict[str, str] = {
            CONF_MASTER_PIN: self._settings_info["settings"]["pins"]["master"]["pin"],
            CONF_DURESS_PIN: self._settings_info["settings"]["pins"]["duress"]["pin"],
        }

        user_pin: dict
        for user_pin in [
            p for p in self._settings_info["settings"]["pins"]["users"] if p["pin"]
        ]:
            pins[user_pin["name"]] = user_pin["pin"]

        return pins
