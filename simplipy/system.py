"""Define a SimpliSafe system (attached to a location)."""
import logging
from enum import Enum
from typing import Dict, Union  # noqa, pylint: disable=unused-import

from .sensor import SensorV2, SensorV3
from .util.string import convert_to_underscore

_LOGGER = logging.getLogger(__name__)


class System:
    """Define a system."""

    class SystemStates(Enum):
        """Define states that the system can be in."""

        away = 1
        away_count = 2
        entry_delay = 3
        exit_delay = 4
        home = 5
        home_count = 5
        off = 6
        unknown = 99

    def __init__(self, api, location_info: dict) -> None:
        """Initialize."""
        self._location_info = location_info
        self.api = api
        self.sensors = {}  # type: Dict[str, Union[SensorV2, SensorV3]]

        try:
            raw_state = location_info['system']['alarmState']
            self._state = self.SystemStates[convert_to_underscore(raw_state)]
        except KeyError:
            _LOGGER.error('Unknown alarm state: %s', raw_state)
            self._state = self.SystemStates.unknown

    @property
    def address(self) -> bool:
        """Return whether the alarm is going off."""
        return self._location_info['street1']

    @property
    def alarm_going_off(self) -> bool:
        """Return whether the alarm is going off."""
        return self._location_info['system']['isAlarming']

    @property
    def serial(self) -> str:
        """Return the system's serial number."""
        return self._location_info['system']['serial']

    @property
    def state(self) -> Enum:
        """Return the current state of the system."""
        return self._state

    @property
    def system_id(self) -> int:
        """Return the SimpliSafe identifier for this system."""
        return self._location_info['sid']

    @property
    def temperature(self) -> int:
        """Return the overall temperature measured by the system."""
        return self._location_info['system']['temperature']

    @property
    def version(self) -> int:
        """Return the system version."""
        return self._location_info['system']['version']

    async def _set_state(self, value: SystemStates) -> None:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()

    async def _update_location_info(self) -> None:
        """Update information on the system."""
        subscription_resp = await self.api.get_subscription_data()
        [location_info] = [
            system['location'] for system in subscription_resp['subscriptions']
            if system['sid'] == self.system_id
        ]
        self._location_info = location_info

    async def get_events(
            self, from_timestamp: int = None, num_events: int = None) -> dict:
        """Get events with optional start time and number of events."""
        params = {}
        if from_timestamp:
            params['fromTimestamp'] = from_timestamp
        if num_events:
            params['numEvents'] = num_events

        resp = await self.api.request(
            'get',
            'subscriptions/{0}/events'.format(self.system_id),
            params=params)

        return resp['events']

    async def set_away(self) -> None:
        """Set the system in "Away" mode."""
        await self._set_state(self.SystemStates.away)

    async def set_home(self) -> None:
        """Set the system in "Home" mode."""
        await self._set_state(self.SystemStates.home)

    async def set_off(self) -> None:
        """Set the system in "Off" mode."""
        await self._set_state(self.SystemStates.off)

    async def update(
            self, refresh_location: bool = True, cached: bool = True) -> None:
        """Raise if calling this undefined based method."""
        raise NotImplementedError()


class SystemV2(System):
    """Define a V2 (original) system."""

    async def _set_state(self, value: Enum) -> None:
        """Set the state of the system."""
        if self._state == value:
            return

        resp = await self.api.request(
            'post',
            'subscriptions/{0}/state'.format(self.system_id),
            params={'state': value.name})

        if resp['success']:
            self._state = self.SystemStates[resp['requestedState']]

    async def update(
            self, refresh_location: bool = True, cached: bool = True) -> None:
        """Update to the latest data (including sensors)."""
        if refresh_location:
            await self._update_location_info()

        sensor_resp = await self.api.request(
            'get',
            'subscriptions/{0}/settings'.format(self.system_id),
            params={
                'settingsType': 'all',
                'cached': str(cached).lower()
            })

        for sensor_data in sensor_resp['settings']['sensors']:
            if not sensor_data:
                continue

            if sensor_data['serial'] in self.sensors:
                sensor = self.sensors[sensor_data['serial']]
                sensor.sensor_data = sensor_data
            else:
                self.sensors[sensor_data['serial']] = SensorV2(sensor_data)


class SystemV3(System):
    """Define a V3 (new) system."""

    async def _set_state(self, value: Enum) -> None:
        """Set the state of the system."""
        if self._state == value:
            return

        resp = await self.api.request(
            'post', 'ss3/subscriptions/{0}/state/{1}'.format(
                self.system_id, value.name))

        self._state = self.SystemStates[convert_to_underscore(resp['state'])]

    async def update(
            self, refresh_location: bool = True, cached: bool = True) -> None:
        """Update sensor data."""
        if refresh_location:
            await self._update_location_info()

        sensor_resp = await self.api.request(
            'get',
            'ss3/subscriptions/{0}/sensors'.format(self.system_id),
            params={'forceUpdate': str(not cached).lower()})

        for sensor_data in sensor_resp['sensors']:
            if sensor_data['serial'] in self.sensors:
                sensor = self.sensors[sensor_data['serial']]
                sensor.sensor_data = sensor_data
            else:
                self.sensors[sensor_data['serial']] = SensorV3(sensor_data)
