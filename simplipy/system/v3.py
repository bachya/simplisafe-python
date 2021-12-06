"""Define a V3 (new) SimpliSafe system."""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Final, cast

import voluptuous as vol

from simplipy.const import LOGGER
from simplipy.device import DeviceTypes
from simplipy.device.camera import Camera
from simplipy.device.lock import Lock
from simplipy.device.sensor.v3 import SensorV3
from simplipy.system import (
    CONF_DURESS_PIN,
    CONF_MASTER_PIN,
    DEFAULT_MAX_USER_PINS,
    System,
    SystemStates,
    get_device_type_from_data,
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

DEFAULT_LOCK_STATE_CHANGE_WINDOW = timedelta(seconds=15)

SYSTEM_PROPERTIES_VALUE_MAP = {
    CONF_ALARM_DURATION: "alarmDuration",
    CONF_ALARM_VOLUME: "alarmVolume",
    CONF_CHIME_VOLUME: "doorChime",
    CONF_ENTRY_DELAY_AWAY: "entryDelayAway",
    CONF_ENTRY_DELAY_HOME: "entryDelayHome",
    CONF_EXIT_DELAY_AWAY: "exitDelayAway",
    CONF_EXIT_DELAY_HOME: "exitDelayHome",
    CONF_LIGHT: "light",
    CONF_VOICE_PROMPT_VOLUME: "voicePrompts",
}

MIN_ALARM_DURATION: Final = 30
MAX_ALARM_DURATION: Final = 480
MIN_ENTRY_DELAY_AWAY: Final = 30
MAX_ENTRY_DELAY_AWAY: Final = 255
MIN_ENTRY_DELAY_HOME: Final = 0
MAX_ENTRY_DELAY_HOME: Final = 255
MIN_EXIT_DELAY_AWAY: Final = 45
MAX_EXIT_DELAY_AWAY: Final = 255
MIN_EXIT_DELAY_HOME: Final = 0
MAX_EXIT_DELAY_HOME: Final = 255


class Volume(Enum):
    """Define a representation of a SimpliSafe volume level."""

    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


SYSTEM_PROPERTIES_PAYLOAD_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ALARM_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_ALARM_DURATION, max=MAX_ALARM_DURATION)
        ),
        vol.Optional(CONF_ALARM_VOLUME): vol.All(Volume, lambda volume: volume.value),
        vol.Optional(CONF_CHIME_VOLUME): vol.All(Volume, lambda volume: volume.value),
        vol.Optional(CONF_ENTRY_DELAY_AWAY): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_ENTRY_DELAY_AWAY, max=MAX_ENTRY_DELAY_AWAY),
        ),
        vol.Optional(CONF_ENTRY_DELAY_HOME): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_ENTRY_DELAY_HOME, max=MAX_ENTRY_DELAY_HOME),
        ),
        vol.Optional(CONF_EXIT_DELAY_AWAY): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_EXIT_DELAY_AWAY, max=MAX_EXIT_DELAY_AWAY)
        ),
        vol.Optional(CONF_EXIT_DELAY_HOME): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_EXIT_DELAY_HOME, max=MAX_EXIT_DELAY_HOME)
        ),
        vol.Optional(CONF_LIGHT): bool,
        vol.Optional(CONF_VOICE_PROMPT_VOLUME): vol.All(
            Volume, lambda volume: volume.value
        ),
    }
)


def create_pin_payload(pins: dict) -> dict[str, dict[str, dict[str, str]]]:
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

    payload["pins"]["users"] = user_pins

    LOGGER.debug("PIN payload: %s", payload)

    return payload


class SystemV3(System):  # pylint: disable=too-many-public-methods
    """Define a V3 (new) system."""

    def __init__(self, api: "API", system_id: int) -> None:
        """Initialize."""
        super().__init__(api, system_id)

        self._last_state_change_dt: datetime | None = None

        # This will be filled in by the appropriate data update methods:
        self.camera_data: dict[str, dict] = self._generate_camera_data()
        self.cameras: dict[str, Camera] = {}
        self.locks: dict[str, Lock] = {}
        self.settings_data: dict[str, dict] = {}

    @property  # type: ignore
    @guard_from_missing_data()
    def alarm_duration(self) -> int:
        """Return the number of seconds an activated alarm will sound for.

        :rtype: ``int``
        """
        return cast(
            int,
            self.settings_data["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["alarm_duration"]
            ],
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def alarm_volume(self) -> Volume:
        """Return the volume level of the alarm.

        :rtype: ``int``
        """
        return Volume(
            int(
                self.settings_data["settings"]["normal"][
                    SYSTEM_PROPERTIES_VALUE_MAP["alarm_volume"]
                ]
            )
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def battery_backup_power_level(self) -> int:
        """Return the power rating of the battery backup.

        :rtype: ``int``
        """
        return cast(int, self.settings_data["basestationStatus"]["backupBattery"])

    @property  # type: ignore
    @guard_from_missing_data()
    def chime_volume(self) -> Volume:
        """Return the volume level of the door chime.

        :rtype: ``int``
        """
        return Volume(
            int(
                self.settings_data["settings"]["normal"][
                    SYSTEM_PROPERTIES_VALUE_MAP["chime_volume"]
                ]
            )
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def entry_delay_away(self) -> int:
        """Return the number of seconds to delay when returning to an "away" alarm.

        :rtype: ``int``
        """
        return cast(
            int,
            self.settings_data["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["entry_delay_away"]
            ],
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def entry_delay_home(self) -> int:
        """Return the number of seconds to delay when returning to an "home" alarm.

        :rtype: ``int``
        """
        return cast(
            int,
            self.settings_data["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["entry_delay_home"]
            ],
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def exit_delay_away(self) -> int:
        """Return the number of seconds to delay when exiting an "away" alarm.

        :rtype: ``int``
        """
        return cast(
            int,
            self.settings_data["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["exit_delay_away"]
            ],
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def exit_delay_home(self) -> int:
        """Return the number of seconds to delay when exiting an "home" alarm.

        :rtype: ``int``
        """
        return cast(
            int,
            self.settings_data["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["exit_delay_home"]
            ],
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def gsm_strength(self) -> int:
        """Return the signal strength of the cell antenna.

        :rtype: ``int``
        """
        return cast(int, self.settings_data["basestationStatus"]["gsmRssi"])

    @property  # type: ignore
    @guard_from_missing_data()
    def light(self) -> bool:
        """Return whether the base station light is on.

        :rtype: ``bool``
        """
        return cast(
            bool,
            self.settings_data["settings"]["normal"][
                SYSTEM_PROPERTIES_VALUE_MAP["light"]
            ],
        )

    @property  # type: ignore
    @guard_from_missing_data(False)
    def offline(self) -> bool:
        """Return whether the system is offline.

        :rtype: ``bool``
        """
        return cast(
            bool,
            self._api.subscription_data[self._sid]["location"]["system"]["isOffline"],
        )

    @property  # type: ignore
    @guard_from_missing_data(False)
    def power_outage(self) -> bool:
        """Return whether the system is experiencing a power outage.

        :rtype: ``bool``
        """
        return cast(
            bool,
            self._api.subscription_data[self._sid]["location"]["system"]["powerOutage"],
        )

    @property  # type: ignore
    @guard_from_missing_data(False)
    def rf_jamming(self) -> bool:
        """Return whether the base station is noticing RF jamming.

        :rtype: ``bool``
        """
        return cast(bool, self.settings_data["basestationStatus"]["rfJamming"])

    @property  # type: ignore
    @guard_from_missing_data()
    def voice_prompt_volume(self) -> Volume:
        """Return the volume level of the voice prompt.

        :rtype: ``int``
        """
        return Volume(
            int(
                self.settings_data["settings"]["normal"][
                    SYSTEM_PROPERTIES_VALUE_MAP["voice_prompt_volume"]
                ]
            )
        )

    @property  # type: ignore
    @guard_from_missing_data()
    def wall_power_level(self) -> int:
        """Return the power rating of the A/C outlet.

        :rtype: ``int``
        """
        return cast(int, self.settings_data["basestationStatus"]["wallPower"])

    @property  # type: ignore
    @guard_from_missing_data()
    def wifi_ssid(self) -> str:
        """Return the ssid of the base station.

        :rtype: ``str``
        """
        return cast(str, self.settings_data["settings"]["normal"]["wifiSSID"])

    @property  # type: ignore
    @guard_from_missing_data()
    def wifi_strength(self) -> int:
        """Return the signal strength of the wifi antenna.

        :rtype: ``int``
        """
        return cast(int, self.settings_data["basestationStatus"]["wifiRssi"])

    async def _async_clear_notifications(self) -> None:
        """Clear active notifications."""
        await self._api.async_request(
            "delete", f"ss3/subscriptions/{self.system_id}/messages"
        )

    async def _async_set_state(self, value: SystemStates) -> None:
        """Set the state of the system."""
        await self._api.async_request(
            "post", f"ss3/subscriptions/{self.system_id}/state/{value.name.lower()}"
        )

        self._state = value
        self._last_state_change_dt = datetime.utcnow()

    async def _async_set_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        self.settings_data = await self._api.async_request(
            "post",
            f"ss3/subscriptions/{self.system_id}/settings/pins",
            json=create_pin_payload(pins),
        )

    async def _async_update_device_data(self, cached: bool = True) -> None:
        """Update sensors to the latest values."""
        sensor_resp = await self._api.async_request(
            "get",
            f"ss3/subscriptions/{self.system_id}/sensors",
            params={"forceUpdate": str(not cached).lower()},
        )
        self.sensor_data = {
            sensor["serial"]: sensor for sensor in sensor_resp.get("sensors", [])
        }

    async def _async_update_settings_data(self, cached: bool = True) -> None:
        """Get all system settings."""
        settings_resp = await self._api.async_request(
            "get",
            f"ss3/subscriptions/{self.system_id}/settings/normal",
            params={"forceUpdate": str(not cached).lower()},
        )

        if settings_resp:
            self.settings_data = settings_resp

    async def _async_update_subscription_data(self) -> None:
        """Update subscription data."""
        await super()._async_update_subscription_data()
        self.camera_data = self._generate_camera_data()

    def _generate_camera_data(self) -> dict[str, dict]:
        """Generate usable, hashable camera data from subscription data.

        This method exists because the SimpliSafe API includes camera data with the
        subscription (and not with other devices); by splitting this out, we can
        separate this action from updating the subscription data itself.
        """
        return {
            camera["uuid"]: camera
            for camera in self._api.subscription_data[self._sid]["location"][
                "system"
            ].get("cameras", [])
        }

    def generate_device_objects(self) -> None:
        """Generate device objects for this system."""
        for serial, sensor in self.sensor_data.items():
            sensor_type = get_device_type_from_data(sensor)
            if sensor_type == DeviceTypes.LOCK:
                self.locks[serial] = Lock(
                    self._api.async_request, self, sensor_type, serial
                )
            else:
                self.sensors[serial] = SensorV3(self, sensor_type, serial)

        for serial in self.camera_data:
            self.cameras[serial] = Camera(self, DeviceTypes.CAMERA, serial)

    async def async_get_pins(self, cached: bool = True) -> dict[str, str]:
        """Return all of the set PINs, including master and duress.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param cached: Whether to used cached data.
        :type cached: ``bool``
        :rtype: ``dict[str, str]``
        """
        await self._async_update_settings_data(cached)

        pins = {
            CONF_MASTER_PIN: self.settings_data["settings"]["pins"]["master"]["pin"],
            CONF_DURESS_PIN: self.settings_data["settings"]["pins"]["duress"]["pin"],
        }

        for user_pin in [
            p for p in self.settings_data["settings"]["pins"]["users"] if p["pin"]
        ]:
            pins[user_pin["name"]] = user_pin["pin"]

        return pins

    async def async_set_properties(
        self, properties: dict[str, bool | int | Volume]
    ) -> None:
        """Set various system properties.

        Volume properties should take values from :meth:`simplipy.system.v3.Volume`.

        The following properties can be set:
           1. alarm_duration (in seconds): 30-480
           2. alarm_volume: Volume.OFF, Volume.LOW, Volume.MEDIUM, Volume.HIGH
           3. chime_volume: Volume.OFF, Volume.LOW, Volume.MEDIUM, Volume.HIGH
           4. entry_delay_away (in seconds): 30-255
           5. entry_delay_home (in seconds): 0-255
           6. exit_delay_away (in seconds): 45-255
           7. exit_delay_home (in seconds): 0-255
           8. light: True or False
           9. voice_prompt_volume: Volume.OFF, Volume.LOW, Volume.MEDIUM, Volume.HIGH

        :param properties: The system properties to set.
        :type properties: ``dict``
        """
        try:
            parsed_properties = SYSTEM_PROPERTIES_PAYLOAD_SCHEMA(properties)
        except vol.Invalid as err:
            raise ValueError(
                f"Using invalid values for system properties ({properties}): {err}"
            ) from None

        settings_resp = await self._api.async_request(
            "post",
            f"ss3/subscriptions/{self.system_id}/settings/normal",
            json={
                "normal": {
                    SYSTEM_PROPERTIES_VALUE_MAP[prop]: value
                    for prop, value in parsed_properties.items()
                }
            },
        )

        if settings_resp:
            self.settings_data = settings_resp

    async def async_update(
        self,
        *,
        include_subscription: bool = True,
        include_settings: bool = True,
        include_devices: bool = True,
        cached: bool = True,
    ) -> None:
        """Get the latest system data.

        The ``cached`` parameter determines whether the SimpliSafe Cloud uses the last
        known values retrieved from the base station (``True``) or retrieves new data.

        :param include_subscription: Whether system state/properties should be updated
        :type include_subscription: ``bool``
        :param include_settings: Whether system settings (like PINs) should be updated
        :type include_settings: ``bool``
        :param include_devices: whether sensors/locks/etc. should be updated
        :type include_devices: ``bool``
        :param cached: Whether to used cached data.
        :type cached: ``bool``
        """
        if (
            self.locks
            and self._last_state_change_dt
            and datetime.utcnow()
            <= self._last_state_change_dt + DEFAULT_LOCK_STATE_CHANGE_WINDOW
        ):
            # The SimpliSafe cloud API currently has a bug wherein systems with locks
            # will audible announce that those locks aren't responding when the system
            # is updated within a certain window (around 15 seconds) of the system
            # changing state. Oof. So, we refuse to update inside that window:
            LOGGER.info(
                "Skipping system update within %s seconds from last system arm/disarm",
                DEFAULT_LOCK_STATE_CHANGE_WINDOW,
            )
            return

        await super().async_update(
            include_subscription=include_subscription,
            include_settings=include_settings,
            include_devices=include_devices,
            cached=cached,
        )
