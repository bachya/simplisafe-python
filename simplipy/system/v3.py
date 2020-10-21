"""Define a V3 (new) SimpliSafe system."""
from typing import TYPE_CHECKING, Dict

import voluptuous as vol

from simplipy.camera import Camera
from simplipy.system import (
    CONF_DURESS_PIN,
    CONF_MASTER_PIN,
    DEFAULT_MAX_USER_PINS,
    System,
    SystemStates,
    coerce_state_from_raw_value,
    guard_from_missing_data,
)

if TYPE_CHECKING:
    from simplipy.api import API

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


def create_pin_payload(pins: dict) -> Dict[str, Dict[str, Dict[str, str]]]:
    """Create the request payload to send for updating PINs."""
    duress_pin = pins.pop(CONF_DURESS_PIN)
    master_pin = pins.pop(CONF_MASTER_PIN)

    payload = {
        "pins": {
            CONF_DURESS_PIN: {"pin": duress_pin},
            CONF_MASTER_PIN: {"pin": master_pin},
        }
    }

    user_pins = {}
    for idx, (label, pin) in enumerate(pins.items()):
        user_pins[str(idx)] = {"name": label, "pin": pin}

    empty_user_index = len(pins)
    for idx in range(DEFAULT_MAX_USER_PINS - empty_user_index):
        user_pins[str(idx + empty_user_index)] = {
            "name": "",
            "pin": "",
        }

    payload["users"] = user_pins

    return payload


class SystemV3(System):
    """Define a V3 (new) system."""

    def __init__(self, api: "API", system_id: int) -> None:
        """Initialize."""
        super().__init__(api, system_id)

        # This will be filled in by the appropriate data update methods:
        self.camera_data: Dict[str, dict] = {}
        self.settings_data: Dict[str, dict] = {}

        self.cameras: Dict[str, Camera] = {}
        self._update_camera_data()

    @property  # type: ignore
    @guard_from_missing_data()
    def alarm_duration(self) -> int:
        """Return the number of seconds an activated alarm will sound for.

        :rtype: ``int``
        """
        return self.settings_data["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["alarm_duration"]
        ]

    @property  # type: ignore
    @guard_from_missing_data()
    def alarm_volume(self) -> int:
        """Return the volume level of the alarm.

        :rtype: ``int``
        """
        return int(
            self.settings_data["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["alarm_volume"]
            ]
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def battery_backup_power_level(self) -> int:
        """Return the power rating of the battery backup.

        :rtype: ``int``
        """
        return self.settings_data["basestationStatus"]["backupBattery"]

    @property  # type: ignore
    @guard_from_missing_data()
    def chime_volume(self) -> int:
        """Return the volume level of the door chime.

        :rtype: ``int``
        """
        return int(
            self.settings_data["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["chime_volume"]
            ]
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def entry_delay_away(self) -> int:
        """Return the number of seconds to delay when returning to an "away" alarm.

        :rtype: ``int``
        """
        return self.settings_data["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["entry_delay_away"]
        ]

    @property  # type: ignore
    @guard_from_missing_data()
    def entry_delay_home(self) -> int:
        """Return the number of seconds to delay when returning to an "home" alarm.

        :rtype: ``int``
        """
        return self.settings_data["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["entry_delay_home"]
        ]

    @property  # type: ignore
    @guard_from_missing_data()
    def exit_delay_away(self) -> int:
        """Return the number of seconds to delay when exiting an "away" alarm.

        :rtype: ``int``
        """
        return self.settings_data["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["exit_delay_away"]
        ]

    @property  # type: ignore
    @guard_from_missing_data()
    def exit_delay_home(self) -> int:
        """Return the number of seconds to delay when exiting an "home" alarm.

        :rtype: ``int``
        """
        return self.settings_data["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["exit_delay_home"]
        ]

    @property  # type: ignore
    @guard_from_missing_data()
    def gsm_strength(self) -> int:
        """Return the signal strength of the cell antenna.

        :rtype: ``int``
        """
        return self.settings_data["basestationStatus"]["gsmRssi"]

    @property  # type: ignore
    @guard_from_missing_data()
    def light(self) -> bool:
        """Return whether the base station light is on.

        :rtype: ``bool``
        """
        return self.settings_data["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["light"]
        ]

    @property  # type: ignore
    @guard_from_missing_data(True)
    def offline(self) -> bool:
        """Return whether the system is offline.

        :rtype: ``bool``
        """
        return self.system_data["location"]["system"]["isOffline"]

    @property  # type: ignore
    @guard_from_missing_data(False)
    def power_outage(self) -> bool:
        """Return whether the system is experiencing a power outage.

        :rtype: ``bool``
        """
        return self.system_data["location"]["system"]["powerOutage"]

    @property  # type: ignore
    @guard_from_missing_data(False)
    def rf_jamming(self) -> bool:
        """Return whether the base station is noticing RF jamming.

        :rtype: ``bool``
        """
        return self.settings_data["basestationStatus"]["rfJamming"]

    @property  # type: ignore
    @guard_from_missing_data()
    def voice_prompt_volume(self) -> int:
        """Return the volume level of the voice prompt.

        :rtype: ``int``
        """
        return self.settings_data["settings"]["normal"][
            SYSTEM_PROPERTIES_VALUE_MAP["voice_prompt_volume"]
        ]

    @property  # type: ignore
    @guard_from_missing_data()
    def wall_power_level(self) -> int:
        """Return the power rating of the A/C outlet.

        :rtype: ``int``
        """
        return self.settings_data["basestationStatus"]["wallPower"]

    @property  # type: ignore
    @guard_from_missing_data()
    def wifi_ssid(self) -> str:
        """Return the ssid of the base station.

        :rtype: ``str``
        """
        return self.settings_data["settings"]["normal"]["wifiSSID"]

    @property  # type: ignore
    @guard_from_missing_data()
    def wifi_strength(self) -> int:
        """Return the signal strength of the wifi antenna.

        :rtype: ``int``
        """
        return self.settings_data["basestationStatus"]["wifiRssi"]

    async def _set_state(self, value: SystemStates) -> None:
        """Set the state of the system."""
        state_resp = await self._api.request(
            "post", f"ss3/subscriptions/{self.system_id}/state/{value.name}"
        )

        self._state = coerce_state_from_raw_value(state_resp["state"])

    async def _set_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        self.settings_data = await self._api.request(
            "post",
            f"ss3/subscriptions/{self.system_id}/settings/pins",
            json=create_pin_payload(pins),
        )

    def _update_camera_data(self) -> None:
        """Update all system data."""
        self.cameras = {}
        for camera in self.system_data["location"]["system"].get("cameras", []):
            uuid = camera["uuid"]
            self.camera_data[uuid] = camera
            self.cameras[uuid] = Camera(self, uuid)

    async def _update_entity_data_internal(self, cached: bool = True) -> None:
        """Update sensors to the latest values."""
        sensor_resp = await self._api.request(
            "get",
            f"ss3/subscriptions/{self.system_id}/sensors",
            params={"forceUpdate": str(not cached).lower()},
        )
        self.entity_data = {
            entity["serial"]: entity for entity in sensor_resp.get("sensors", [])
        }

    async def _update_settings_data(self, cached: bool = True) -> None:
        """Get all system settings."""
        settings_resp = await self._api.request(
            "get",
            f"ss3/subscriptions/{self.system_id}/settings/normal",
            params={"forceUpdate": str(not cached).lower()},
        )

        if settings_resp:
            self.settings_data = settings_resp

    async def _update_system_data(self) -> None:
        """Update all system data."""
        await super()._update_system_data()
        self._update_camera_data()

    async def get_pins(self, cached: bool = True) -> Dict[str, str]:
        """Return all of the set PINs, including master and duress.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param cached: Whether to used cached data.
        :type cached: ``bool``
        :rtype: ``Dict[str, str]``
        """
        await self._update_settings_data(cached)

        pins = {
            CONF_MASTER_PIN: self.settings_data["settings"]["pins"]["master"]["pin"],
            CONF_DURESS_PIN: self.settings_data["settings"]["pins"]["duress"]["pin"],
        }

        for user_pin in [
            p for p in self.settings_data["settings"]["pins"]["users"] if p["pin"]
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

        settings_resp = await self._api.request(
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
            self.settings_data = settings_resp
