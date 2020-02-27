"""Define a V3 (new) SimpliSafe system."""
from enum import Enum
import logging
from typing import Callable, Dict

import voluptuous as vol

from simplipy.system import CONF_DURESS_PIN, CONF_MASTER_PIN, System, create_pin_payload

_LOGGER: logging.Logger = logging.getLogger(__name__)

CONF_ALARM_DURATION = "alarm_duration"
CONF_ALARM_VOLUME = "alarm_volume"
CONF_CHIME_VOLUME = "chime_volume"
CONF_ENTRY_DELAY_AWAY = "entry_delay_away"
CONF_ENTRY_DELAY_HOME = "entry_delay_home"
CONF_EXIT_DELAY_AWAY = "exit_delay_away"
CONF_EXIT_DELAY_HOME = "exit_delay_home"
CONF_LIGHT = "light"
CONF_VOICE_PROMPT_VOLUME = "voice_prompt_volume"

VOLUME_OFF = 0
VOLUME_LOW = 1
VOLUME_MEDIUM = 2
VOLUME_HIGH = 3
VOLUMES = [VOLUME_OFF, VOLUME_LOW, VOLUME_MEDIUM, VOLUME_HIGH]

SYSTEM_PROPERTIES_VALUE_MAP = {
    "alarm_duration": "alarmDuration",
    "alarm_volume": "alarmVolume",
    "chime_volume": "doorChime",
    "entry_delay_away": "entryDelayAway",
    "entry_delay_home": "entryDelayHome",
    "exit_delay_away": "exitDelayAway",
    "exit_delay_home": "exitDelayHome",
    "light": "light",
    "voice_prompt_volume": "voicePrompts",
}

SYSTEM_PROPERTIES_PAYLOAD_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ALARM_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=30, max=480)
        ),
        vol.Optional(CONF_ALARM_VOLUME): vol.All(vol.Coerce(int), vol.In(VOLUMES)),
        vol.Optional(CONF_CHIME_VOLUME): vol.All(vol.Coerce(int), vol.In(VOLUMES)),
        vol.Optional(CONF_ENTRY_DELAY_AWAY): vol.All(
            vol.Coerce(int), vol.Range(min=30, max=255)
        ),
        vol.Optional(CONF_ENTRY_DELAY_HOME): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
        vol.Optional(CONF_EXIT_DELAY_AWAY): vol.All(
            vol.Coerce(int), vol.Range(min=45, max=255)
        ),
        vol.Optional(CONF_EXIT_DELAY_HOME): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
        vol.Optional(CONF_LIGHT): bool,
        vol.Optional(CONF_VOICE_PROMPT_VOLUME): vol.All(
            vol.Coerce(int), vol.In(VOLUMES)
        ),
    }
)


def guard_missing_base_station_status(prop) -> Callable:
    """Define a guard against missing base station status."""

    def decorator(system: "SystemV3") -> None:
        """Decorate."""
        if system.settings_info.get("basestationStatus") is None:
            _LOGGER.error(
                "SimpliSafe cloud didn't return expected data for property %s: %s",
                prop.__name__,
                system.settings_info,
            )
            return None
        return prop(system)

    return decorator


class SystemV3(System):
    """Define a V3 (new) system."""

    def __init__(self, request, get_subscription_data, location_info) -> None:
        """Initialize."""
        super().__init__(request, get_subscription_data, location_info)
        self.settings_info: dict = {}

    @property
    def alarm_duration(self) -> int:
        """Return the number of seconds an activated alarm will sound for.

        :rtype: ``int``
        """
        return self.settings_info["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["alarm_duration"]
        ]

    @property
    def alarm_volume(self) -> int:
        """Return the volume level of the alarm.

        :rtype: ``int``
        """
        return int(
            self.settings_info["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["alarm_volume"]
            ]
        )

    @property  # type: ignore
    @guard_missing_base_station_status
    def battery_backup_power_level(self) -> int:
        """Return the power rating of the battery backup.

        :rtype: ``int``
        """
        return self.settings_info["basestationStatus"]["backupBattery"]

    @property
    def chime_volume(self) -> int:
        """Return the volume level of the door chime.

        :rtype: ``int``
        """
        return int(
            self.settings_info["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["chime_volume"]
            ]
        )

    @property
    def entry_delay_away(self) -> int:
        """Return the number of seconds to delay when returning to an "away" alarm.

        :rtype: ``int``
        """
        return self.settings_info["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["entry_delay_away"]
        ]

    @property
    def entry_delay_home(self) -> int:
        """Return the number of seconds to delay when returning to an "home" alarm.

        :rtype: ``int``
        """
        return self.settings_info["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["entry_delay_home"]
        ]

    @property
    def exit_delay_away(self) -> int:
        """Return the number of seconds to delay when exiting an "away" alarm.

        :rtype: ``int``
        """
        return self.settings_info["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["exit_delay_away"]
        ]

    @property
    def exit_delay_home(self) -> int:
        """Return the number of seconds to delay when exiting an "home" alarm.

        :rtype: ``int``
        """
        return self.settings_info["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["exit_delay_home"]
        ]

    @property  # type: ignore
    @guard_missing_base_station_status
    def gsm_strength(self) -> int:
        """Return the signal strength of the cell antenna.

        :rtype: ``int``
        """
        return self.settings_info["basestationStatus"]["gsmRssi"]

    @property
    def light(self) -> bool:
        """Return whether the base station light is on.

        :rtype: ``bool``
        """
        return self.settings_info["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["light"]
        ]

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

    @property  # type: ignore
    @guard_missing_base_station_status
    def rf_jamming(self) -> bool:
        """Return whether the base station is noticing RF jamming.

        :rtype: ``bool``
        """
        return self.settings_info["basestationStatus"]["rfJamming"]

    @property
    def voice_prompt_volume(self) -> int:
        """Return the volume level of the voice prompt.

        :rtype: ``int``
        """
        return self.settings_info["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["voice_prompt_volume"]
        ]

    @property  # type: ignore
    @guard_missing_base_station_status
    def wall_power_level(self) -> int:
        """Return the power rating of the A/C outlet.

        :rtype: ``int``
        """
        return self.settings_info["basestationStatus"]["wallPower"]

    @property
    def wifi_ssid(self) -> str:
        """Return the ssid of the base station.

        :rtype: ``str``
        """
        return self.settings_info["settings"]["normal"]["wifiSSID"]

    @property  # type: ignore
    @guard_missing_base_station_status
    def wifi_strength(self) -> int:
        """Return the signal strength of the wifi antenna.

        :rtype: ``int``
        """
        return self.settings_info["basestationStatus"]["wifiRssi"]

    async def _get_entities_payload(self, cached: bool = True) -> dict:
        """Update sensors to the latest values."""
        sensor_resp = await self._request(
            "get",
            f"ss3/subscriptions/{self.system_id}/sensors",
            params={"forceUpdate": str(not cached).lower()},
        )

        return sensor_resp.get("sensors", [])

    async def _get_settings(self, cached: bool = True) -> None:
        """Get all system settings."""
        settings_resp: dict = await self._request(
            "get",
            f"ss3/subscriptions/{self.system_id}/settings/normal",
            params={"forceUpdate": str(not cached).lower()},
        )

        if settings_resp:
            self.settings_info = settings_resp

    async def _set_state(self, value: Enum) -> None:
        """Set the state of the system."""
        state_resp: dict = await self._request(
            "post", f"ss3/subscriptions/{self.system_id}/state/{value.name}"
        )

        _LOGGER.debug('Set "%s" response: %s', value.name, state_resp)

        if not state_resp:
            return

        self._state = self._coerce_state_from_string(state_resp["state"])

    async def _set_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        self.settings_info = await self._request(
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
            CONF_MASTER_PIN: self.settings_info["settings"]["pins"]["master"]["pin"],
            CONF_DURESS_PIN: self.settings_info["settings"]["pins"]["duress"]["pin"],
        }

        user_pin: dict
        for user_pin in [
            p for p in self.settings_info["settings"]["pins"]["users"] if p["pin"]
        ]:
            pins[user_pin["name"]] = user_pin["pin"]

        return pins

    async def set_properties(self, properties: dict) -> None:
        """Set various system properties.

        The following properties can be set:
           1. alarm_duration (in seconds): 30-480
           2. alarm_volume: 0 (off), 1 (low), 2 (medium), 3 (high)
           3. chime_volume: 0 (off), 1 (low), 2 (medium), 3 (high)
           4. entry_delay_away (in seconds): 30-255
           5. entry_delay_home (in seconds): 0-255
           6. exit_delay_away (in seconds): 45-255
           7. exit_delay_home (in seconds): 0-255
           8. light: True or False
           9. voice_prompt_volume: 0 (off), 1 (low), 2 (medium), 3 (high)

        :param properties: The system properties to set.
        :type properties: ``dict``
        """
        try:
            SYSTEM_PROPERTIES_PAYLOAD_SCHEMA(properties)
        except vol.Invalid as err:
            raise ValueError(
                f"Using invalid values for system properties ({properties}): {err}"
            ) from None

        settings_resp = await self._request(
            "post",
            f"ss3/subscriptions/{self.system_id}/settings/normal",
            json={
                "normal": {
                    SYSTEM_PROPERTIES_VALUE_MAP[prop]: value
                    for prop, value in properties.items()
                }
            },
        )

        if settings_resp:
            self.settings_info = settings_resp
