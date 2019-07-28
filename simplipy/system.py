"""Define V2 and V3 SimpliSafe systems."""
import asyncio
import logging
from enum import Enum
from typing import Any, Dict, Union

from .errors import InvalidCredentialsError, PinError, SimplipyError
from .sensor import SensorV2, SensorV3
from .util.string import convert_to_underscore

_LOGGER = logging.getLogger(__name__)

CONF_DURESS_PIN = "duress"
CONF_MASTER_PIN = "master"

DEFAULT_MAX_USER_PINS = 4
MAX_PIN_LENGTH = 4

RESERVED_PIN_LABELS = (CONF_DURESS_PIN, CONF_MASTER_PIN)


class SystemStates(Enum):
    """Define states that the system can be in."""

    alarm_count = 1
    away = 2
    away_count = 3
    entry_delay = 4
    error = 5
    exit_delay = 6
    home = 7
    home_count = 8
    off = 9
    unknown = 99


class System:
    """Define a system."""

    def __init__(self, api, location_info: dict) -> None:
        """Initialize."""
        self._location_info = location_info
        self.api = api
        self.sensors = {}  # type: Dict[str, Union[SensorV2, SensorV3]]

        self._state = self._coerce_state_from_string(
            location_info["system"]["alarmState"]
        )

    @property
    def address(self) -> bool:
        """Return the street address of the system."""
        return self._location_info["street1"]

    @property
    def alarm_going_off(self) -> bool:
        """Return whether the alarm is going off."""
        return self._location_info["system"]["isAlarming"]

    @property
    def serial(self) -> str:
        """Return the system's serial number."""
        return self._location_info["system"]["serial"]

    @property
    def state(self) -> Enum:
        """Return the current state of the system."""
        return self._state

    @property
    def system_id(self) -> int:
        """Return the SimpliSafe identifier for this system."""
        return self._location_info["sid"]

    @property
    def temperature(self) -> int:
        """Return the overall temperature measured by the system."""
        return self._location_info["system"]["temperature"]

    @property
    def version(self) -> int:
        """Return the system version."""
        return self._location_info["system"]["version"]

    @staticmethod
    def _coerce_state_from_string(value: str) -> SystemStates:
        """Return a proper state from a string input."""
        try:
            return SystemStates[convert_to_underscore(value)]
        except KeyError:
            _LOGGER.error("Unknown system state: %s", value)
            return SystemStates.unknown

    async def _send_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        raise NotImplementedError()

    async def _set_state(self, value: SystemStates) -> None:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()

    async def _update_location_info(self) -> None:
        """Update information on the system."""
        subscription_resp = await self.api.get_subscription_data()
        [location_info] = [
            system["location"]
            for system in subscription_resp["subscriptions"]
            if system["sid"] == self.system_id
        ]
        self._location_info = location_info
        self._state = self._coerce_state_from_string(
            location_info["system"]["alarmState"]
        )

    async def _update_sensors(self, cached: bool = True) -> None:
        """Update sensors to the latest values."""
        raise NotImplementedError()

    async def _update_settings(self, cached: bool = True) -> None:
        """Update system settings."""
        pass

    async def get_events(
        self, from_timestamp: int = None, num_events: int = None
    ) -> dict:
        """Get events with optional start time and number of events."""
        params = {}
        if from_timestamp:
            params["fromTimestamp"] = from_timestamp
        if num_events:
            params["numEvents"] = num_events

        events_resp = await self.api.request(
            "get", "subscriptions/{0}/events".format(self.system_id), params=params
        )

        _LOGGER.debug("Events response: %s", events_resp)

        return events_resp["events"]

    async def get_latest_event(self) -> dict:
        """Get the most recent system event."""
        events = await self.get_events(num_events=1)
        return events[0]

    async def get_pins(self, cached: bool = True) -> dict:
        """Return all of the set PINs, including master and duress."""
        raise NotImplementedError()

    async def remove_pin(self, pin_or_label: str) -> None:
        """Remove a PIN by its value or label."""
        # Because SimpliSafe's API works by sending the entire payload of PINs, we
        # can't reasonably check a local cache for up-to-date PIN data; so, we fetch the
        # latest each time:
        latest_pins = await self.get_pins(cached=False)

        if pin_or_label in RESERVED_PIN_LABELS:
            raise PinError("Refusing to delete reserved PIN: {0}".format(pin_or_label))

        try:
            label = next((k for k, v in latest_pins.items() if pin_or_label in (k, v)))
        except StopIteration:
            raise PinError("Cannot delete nonexistent PIN: {0}".format(pin_or_label))

        del latest_pins[label]

        await self._send_updated_pins(latest_pins)

    async def set_away(self) -> None:
        """Set the system in "Away" mode."""
        await self._set_state(SystemStates.away)

    async def set_home(self) -> None:
        """Set the system in "Home" mode."""
        await self._set_state(SystemStates.home)

    async def set_off(self) -> None:
        """Set the system in "Off" mode."""
        await self._set_state(SystemStates.off)

    async def set_pin(self, label: str, pin: str) -> None:
        """Set a PIN."""
        if len(pin) != MAX_PIN_LENGTH:
            raise PinError("PINs must be {0} digits long".format(MAX_PIN_LENGTH))

        try:
            int(pin)
        except ValueError:
            raise PinError("PINs can only contain numbers")

        # Because SimpliSafe's API works by sending the entire payload of PINs, we
        # can't reasonably check a local cache for up-to-date PIN data; so, we fetch the
        # latest each time.
        latest_pins = await self.get_pins(cached=False)

        if pin in latest_pins.values():
            raise PinError("Refusing to create duplicate PIN: {0}".format(pin))

        max_pins = DEFAULT_MAX_USER_PINS + len(RESERVED_PIN_LABELS)
        if len(latest_pins) == max_pins and label not in RESERVED_PIN_LABELS:
            raise PinError(
                "Refusing to create more than {0} user PINs".format(max_pins)
            )

        latest_pins[label] = pin

        await self._send_updated_pins(latest_pins)

    async def update(self, refresh_location: bool = True, cached: bool = True) -> None:
        """Update to the latest data (including sensors)."""
        tasks = {
            "sensors": self._update_sensors(cached),
            "settings": self._update_settings(cached),
        }
        if refresh_location:
            tasks[  # pylint: disable=assignment-from-no-return
                "location"
            ] = self._update_location_info()

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for operation, result in zip(tasks, results):
            if isinstance(result, InvalidCredentialsError):
                raise result
            if isinstance(result, SimplipyError):
                _LOGGER.error("Error while retrieving %s: %s", operation, result)


class SystemV2(System):
    """Define a V2 (original) system."""

    @staticmethod
    def _create_pin_payload(pins: dict) -> dict:
        """Transform the internal PINs structure to a V2-compatible payload."""
        payload = {
            "pins": {
                CONF_DURESS_PIN: {"value": pins.pop(CONF_DURESS_PIN)},
                "pin1": {"value": pins.pop(CONF_MASTER_PIN)},
            }
        }

        for idx, (label, pin) in enumerate(pins.items()):
            payload["pins"]["pin{0}".format(idx + 2)] = {"name": label, "value": pin}

        empty_user_index = len(pins)
        for idx in range(DEFAULT_MAX_USER_PINS - empty_user_index):
            payload["pins"]["pin{0}".format(str(idx + 2 + empty_user_index))] = {
                "name": "",
                "pin": "",
            }

        return payload

    async def _send_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        await self.api.request(
            "post",
            "subscriptions/{0}/pins".format(self.system_id),
            json=self._create_pin_payload(pins),
        )

    async def _set_state(self, value: Enum) -> None:
        """Set the state of the system."""
        if self._state == value:
            return

        state_resp = await self.api.request(
            "post",
            "subscriptions/{0}/state".format(self.system_id),
            params={"state": value.name},
        )

        _LOGGER.debug('Set "%s" response: %s', value.name, state_resp)

        if not state_resp:
            return

        if state_resp["success"]:
            self._state = SystemStates[state_resp["requestedState"]]

    async def _update_sensors(self, cached: bool = True) -> None:
        """Update sensors to the latest values."""
        sensor_resp = await self.api.request(
            "get",
            "subscriptions/{0}/settings".format(self.system_id),
            params={"settingsType": "all", "cached": str(cached).lower()},
        )

        _LOGGER.debug("Sensor response: %s", sensor_resp)

        if not sensor_resp:
            return

        for sensor_data in sensor_resp["settings"]["sensors"]:
            if not sensor_data:
                continue

            if sensor_data["serial"] in self.sensors:
                sensor = self.sensors[sensor_data["serial"]]
                sensor.sensor_data = sensor_data
            else:
                self.sensors[sensor_data["serial"]] = SensorV2(sensor_data)

    async def get_pins(self, cached: bool = True) -> Dict[str, str]:
        """Return all of the set PINs, including master and duress."""
        pins_resp = await self.api.request(
            "get",
            "subscriptions/{0}/pins".format(self.system_id),
            params={"settingsType": "all", "cached": str(cached).lower()},
        )

        pins = {
            CONF_MASTER_PIN: pins_resp["pins"].pop("pin1")["value"],
            CONF_DURESS_PIN: pins_resp["pins"].pop("duress")["value"],
        }

        for user_pin in [p for p in pins_resp["pins"].values() if p["value"]]:
            pins[user_pin["name"]] = user_pin["value"]

        return pins


class SystemV3(System):
    """Define a V3 (new) system."""

    def __init__(self, api, location_info: dict) -> None:
        """Initialize."""
        super().__init__(api, location_info)
        self._settings_info = {}  # type: Dict[str, Any]

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

    @staticmethod
    def _create_pin_payload(pins: dict) -> dict:
        """Transform the internal PINs structure to a V3-compatible payload."""
        payload = {
            "pins": {
                CONF_DURESS_PIN: {"pin": pins.pop(CONF_DURESS_PIN)},
                CONF_MASTER_PIN: {"pin": pins.pop(CONF_MASTER_PIN)},
                "users": {},
            }
        }  # type: Dict[str, Any]

        for idx, (label, pin) in enumerate(pins.items()):
            payload["pins"]["users"][str(idx)] = {"name": label, "pin": pin}

        empty_user_index = len(pins)
        for idx in range(DEFAULT_MAX_USER_PINS - empty_user_index):
            payload["pins"]["users"][str(idx + empty_user_index)] = {
                "name": "",
                "pin": "",
            }

        return payload

    async def _send_updated_pins(self, pins: dict) -> None:
        """Post new PINs."""
        self._settings_info = await self.api.request(
            "post",
            "ss3/subscriptions/{0}/settings/pins".format(self.system_id),
            json=self._create_pin_payload(pins),
        )

    async def _set_state(self, value: Enum) -> None:
        """Set the state of the system."""
        if self._state == value:
            return

        state_resp = await self.api.request(
            "post", "ss3/subscriptions/{0}/state/{1}".format(self.system_id, value.name)
        )

        _LOGGER.debug('Set "%s" response: %s', value.name, state_resp)

        if not state_resp:
            return

        self._state = self._coerce_state_from_string(state_resp["state"])

    async def _update_sensors(self, cached: bool = True) -> None:
        """Update sensors to the latest values."""
        sensor_resp = await self.api.request(
            "get",
            "ss3/subscriptions/{0}/sensors".format(self.system_id),
            params={"forceUpdate": str(not cached).lower()},
        )

        _LOGGER.debug("Sensor response: %s", sensor_resp)

        if not sensor_resp:
            return

        for sensor_data in sensor_resp["sensors"]:
            if sensor_data["serial"] in self.sensors:
                sensor = self.sensors[sensor_data["serial"]]
                sensor.sensor_data = sensor_data
            else:
                self.sensors[sensor_data["serial"]] = SensorV3(sensor_data)

    async def _update_settings(self, cached: bool = True) -> None:
        """Update system settings."""
        settings_resp = await self.api.request(
            "get",
            "ss3/subscriptions/{0}/settings/pins".format(self.system_id),
            params={"forceUpdate": str(not cached).lower()},
        )

        if settings_resp:
            self._settings_info = settings_resp

    async def get_pins(self, cached: bool = True) -> Dict[str, str]:
        """Return all of the set PINs, including master and duress."""
        await self._update_settings(cached)

        pins = {
            CONF_MASTER_PIN: self._settings_info["settings"]["pins"]["master"]["pin"],
            CONF_DURESS_PIN: self._settings_info["settings"]["pins"]["duress"]["pin"],
        }

        for user_pin in [
            p for p in self._settings_info["settings"]["pins"]["users"] if p["pin"]
        ]:
            pins[user_pin["name"]] = user_pin["pin"]

        return pins
