"""
SimpliSafe Alarm object.
"""
import logging

_LOGGER = logging.getLogger(__name__)


class SimpliSafeSystem(object):
    """
    Represents a SimpliSafe alarm system.
    """

    def __init__(self, api_interface, location_id, state=None):
        """
        Alarm object.

        Args:
            api_interfce (object): The API object to handle communication
                                   to and from the API.
            location_id (str): The location id to change the state of.
            state (str): The the initial state of the system.
        """
        self.api = api_interface
        self.location_id = location_id
        self.session_id = None
        self.uid = None
        self.system_state = state
        self.update()

    def state(self):
        """
        Return the current state of the system. (str)
        """
        return self.system_state

    def temperature(self):
        """
        Return the current temperature of the system.
        Will return null if API doesn't return an int.
        """
        try:
            api_temp = self.sensors.get("freeze").get("temp")
            if api_temp != "?":
                return int(api_temp)
            else:
                return None
        except:
            _LOGGER.error("Could not get current temperature")
            return None

    def carbon_monoxide(self):
        """
        Current state of CO sensor.
        """
        try:
            return self.sensors.get("recent_co").get("text")
        except:
            _LOGGER.error("Could not get carbon monoxide detector state")
            return None

    def flood(self):
        """
        Current state of flood sensor.
        """
        try:
            return self.sensors.get("recent_flood").get("text")
        except:
            _LOGGER.error("Could not get flood detector state")
            return None

    def fire(self):
        """
        Current state of fire detector.
        """
        try:
            return self.sensors.get("recent_fire").get("text")
        except:
            _LOGGER.error("Could not get smoke detector state")
            return None

    def alarm(self):
        """
        Current state of recent alarm.
        """
        try:
            return self.sensors.get("recent_alarm").get("text")
        except:
            _LOGGER.error("Could not get last alarm state")
            return None

    def last_event(self):
        """
        Return the last event sent by the system.
        """
        try:
            return self.events.get("events")[0].get("event_desc")
        except:
            _LOGGER.error("Could not get last event")
            return None

    def update(self, retry=True):
        """
        Fetch all of the latest states from the API.
        """
        try:
            dashboard = self.api.get_state(self.location_id, "dashboard")
            self.sensors = dashboard["location"]["monitoring"]
            self.events = self.api.get_state(self.location_id, "events")
            self.system_state = dashboard["location"]["system"].get('state')
        except ValueError:
            if retry:
                _LOGGER.error("Invalid response from API. Attempting to log in again.")
                self.api.login()
                self.update(False)

    def set_state(self, state, retry=True):
        """
        Set the state of the alarm system.
        """
        try:
            self.api.set_device_state(self.location_id, state)
        except ValueError:
            if retry:
                _LOGGER.error("Invalid response from API. Attempting to log in again.")
                self.api.login()
                self.set_state(state, False)
