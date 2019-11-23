"""Define a V3 (new) SimpliSafe system."""
from enum import Enum
import logging
from typing import Any, Dict

from simplipy.system import CONF_DURESS_PIN, CONF_MASTER_PIN, System, create_pin_payload

_LOGGER: logging.Logger = logging.getLogger(__name__)


class LevelMap(Enum):
    """A way to map off/low/medium/high values to V3-compatible integers."""

    off = 0
    low = 1
    medium = 2
    high = 3


class SystemV3(System):  # pylint: disable=too-many-public-methods
    """Define a V3 (new) system."""

    def __init__(self, request, get_subscription_data, location_info) -> None:
        """Initialize."""
        super().__init__(request, get_subscription_data, location_info)
        self._settings_info: dict = {}

    @property
    def alarm_duration(self) -> int:
        """Return the number of seconds an activated alarm will sound for.

        :rtype: ``int``
        """
        return self._settings_info["settings"]["normal"]["alarmDuration"]

    @property
    def alarm_volume(self) -> LevelMap:
        """Return the volume level of the alarm.

        :rtype: :meth:`simplipy.system.v3.LevelMap`
        """
        return LevelMap(self._settings_info["settings"]["normal"]["alarmVolume"])

    @property
    def battery_backup_power_level(self) -> int:
        """Return the power rating of the battery backup.

        :rtype: ``int``
        """
        return self._settings_info["basestationStatus"]["backupBattery"]

    @property
    def chime_volume(self) -> LevelMap:
        """Return the volume level of the door chime.

        :rtype: :meth:`simplipy.system.v3.LevelMap`
        """
        return LevelMap(self._settings_info["settings"]["normal"]["doorChime"])

    @property
    def entry_delay_away(self) -> int:
        """Return the number of seconds to delay when returning to an "away" alarm.

        :rtype: ``int``
        """
        return self._settings_info["settings"]["normal"]["entryDelayAway"]

    @property
    def entry_delay_home(self) -> int:
        """Return the number of seconds to delay when returning to an "home" alarm.

        :rtype: ``int``
        """
        return self._settings_info["settings"]["normal"]["entryDelayHome"]

    @property
    def exit_delay_away(self) -> int:
        """Return the number of seconds to delay when exiting an "away" alarm.

        :rtype: ``int``
        """
        return self._settings_info["settings"]["normal"]["exitDelayAway"]

    @property
    def exit_delay_home(self) -> int:
        """Return the number of seconds to delay when exiting an "home" alarm.

        :rtype: ``int``
        """
        return self._settings_info["settings"]["normal"]["exitDelayHome"]

    @property
    def gsm_strength(self) -> int:
        """Return the signal strength of the cell antenna.

        :rtype: ``int``
        """
        return self._settings_info["basestationStatus"]["gsmRssi"]

    @property
    def light(self) -> bool:
        """Return whether the base station light is on.

        :rtype: ``bool``
        """
        return self._settings_info["settings"]["normal"]["light"]

    @property
    def offline(self) -> bool:
        """Return whether the system is offline.

        :rtype: ``bool``
        """
        return self._location_info["system"]["isOffline"]

    @property
    def power_outage(self) -> bool:
        """Return whether the system is experiencing a power outage.

        :rtype: ``bool``
        """
        return self._location_info["system"]["powerOutage"]

    @property
    def rf_jamming(self) -> bool:
        """Return whether the base station is noticing RF jamming.

        :rtype: ``bool``
        """
        return self._settings_info["basestationStatus"]["rfJamming"]

    @property
    def voice_prompt_volume(self) -> LevelMap:
        """Return the volume level of the voice prompt.

        :rtype: :meth:`simplipy.system.v3.LevelMap`
        """
        return LevelMap(self._settings_info["settings"]["normal"]["voicePrompts"])

    @property
    def wall_power_level(self) -> int:
        """Return the power rating of the A/C outlet.

        :rtype: ``int``
        """
        return self._settings_info["basestationStatus"]["wallPower"]

    @property
    def wifi_ssid(self) -> str:
        """Return the ssid of the base station.

        :rtype: ``str``
        """
        return self._settings_info["settings"]["normal"]["wifiSSID"]

    @property
    def wifi_strength(self) -> int:
        """Return the signal strength of the wifi antenna.

        :rtype: ``int``
        """
        return self._settings_info["basestationStatus"]["wifiRssi"]

    async def _get_entities_payload(self, cached: bool = True) -> dict:
        """Update sensors to the latest values."""
        sensor_resp = await self._request(
            "get",
            f"ss3/subscriptions/{self.system_id}/sensors",
            params={"forceUpdate": str(not cached).lower()},
        )

        return sensor_resp["sensors"]

    async def _get_settings(self, cached: bool = True) -> None:
        """Get all system settings."""
        settings_resp: dict = await self._request(
            "get",
            f"ss3/subscriptions/{self.system_id}/settings/normal",
            params={"forceUpdate": str(not cached).lower()},
        )

        if settings_resp:
            self._settings_info = settings_resp

    async def _set_state(self, value: Enum) -> None:
        """Set the state of the system."""
        state_resp: dict = await self._request(
            "post", f"ss3/subscriptions/{self.system_id}/state/{value.name}"
        )

        _LOGGER.debug('Set "%s" response: %s', value.name, state_resp)

        if not state_resp:
            return

        self._state = self._coerce_state_from_string(state_resp["state"])

    async def _set_system_property(self, property_name: str, value: Any) -> None:
        """Set a system property (by SimpliSafe name) in the remote API."""
        payload = {}
        if isinstance(value, LevelMap):
            payload[property_name] = value.value
        else:
            payload[property_name] = value

        settings_resp = await self._request(
            "post", f"ss3/subscriptions/{self.system_id}/settings/normal", json=payload
        )

        if settings_resp:
            self._settings_info = settings_resp

    async def _set_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        self._settings_info = await self._request(
            "post",
            f"ss3/subscriptions/{self.system_id}/settings/pins",
            json=create_pin_payload(pins),
        )

    async def get_pins(self, cached: bool = True) -> Dict[str, str]:
        """Return all of the set PINs, including master and duress.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param cached: Whether to used cached data.
        :type cached: ``bool``
        :rtype: ``Dict[str, str]``
        """
        await self._get_settings(cached)

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

    async def set_alarm_duration(self, duration: int) -> None:
        """Set the duration of an active alarm.

        :param duration: The number of seconds to sound an alarm.
        :type duration: ``int``
        """
        await self._set_system_property("alarmDuration", duration)

    async def set_alarm_volume(self, level: LevelMap) -> None:
        """Set the volume level of the alarm siren.

        :param level: The volume level to set.
        :type level: :meth:`simplipy.system.v3.LevelMap`
        """
        await self._set_system_property("alarmDuration", level)

    async def set_chime_volume(self, level: LevelMap) -> None:
        """Set the volume level of the chime.

        :param level: The volume level to set.
        :type level: :meth:`simplipy.system.v3.LevelMap`
        """
        await self._set_system_property("doorChime", level)

    async def set_entry_delay_away(self, duration: int) -> None:
        """Set the duration of the entry delay ("away" mode).

        :param duration: The number of seconds to delay.
        :type duration: ``int``
        """
        await self._set_system_property("entryDelayAway", duration)

    async def set_entry_delay_home(self, duration: int) -> None:
        """Set the duration of the entry delay ("home" mode).

        :param duration: The number of seconds to delay.
        :type duration: ``int``
        """
        await self._set_system_property("entryDelayHome", duration)

    async def set_exit_delay_away(self, duration: int) -> None:
        """Set the duration of the exit delay ("away" mode).

        :param duration: The number of seconds to delay.
        :type duration: ``int``
        """
        await self._set_system_property("exitDelayAway", duration)

    async def set_exit_delay_home(self, duration: int) -> None:
        """Set the duration of the exit delay ("home" mode).

        :param duration: The number of seconds to delay.
        :type duration: ``int``
        """
        await self._set_system_property("exitDelayHome", duration)

    async def set_light(self, is_on: bool) -> None:
        """Set whether the base station light is on.

        :param is_on: ``True`` if on, ``False`` if off.
        :type duration: ``bool``
        """
        await self._set_system_property("light", is_on)

    async def set_voice_prompt_volume(self, level: LevelMap) -> None:
        """Set the volume level of voice prompts.

        :param level: The volume level to set.
        :type level: :meth:`simplipy.system.v3.LevelMap`
        """
        await self._set_system_property("voicePrompts", level)
