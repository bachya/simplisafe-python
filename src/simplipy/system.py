"""
SimpliSafe Alarm object.
"""
import logging

_LOGGER = logging.getLogger(__name__)

from simplipy.sensor import SimpliSafeSensor


class SimpliSafeSystem(object):
    """
    Represents a SimpliSafe alarm system.
    """

    def __init__(self, api_interface, system_dict, sensor_list):
        """
        Alarm object.

        Args:
            api_interfce (object): The API object to handle communication
                                   to and from the API.
            system_dict (dict): The system's current state.
        """
        self.api = api_interface
        self.location_id = system_dict["sid"]
        self.state = system_dict["alarmState"]
        self.alarm_active = system_dict["isAlarming"]
        self.temperature = system_dict["temperature"]
        self.version = system_dict["version"]
        self.sensors = []
        for sensor in sensor_list:
            if bool(sensor):
                self.sensors.append(SimpliSafeSensor(api_interface, sensor))

    def state(self):
        """
        Return the current state of the system. (str)
        """
        return self.state

    def temperature(self):
        """
        Return the current temperature of the system.
        """
        return self.temperature


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
        self.api._get_subscriptions()
        response = self.api._get_system_state()
        self.location_id = response["sid"]
        self.state = response["alarmState"]
        self.alarm_active = response["isAlarming"]
        self.temperature = response["temperature"]

    def set_state(self, state, retry=True):
        """
        Set the state of the alarm system.
        """
        if self.api.set_state(state):
            _LOGGER.debug("Successfuly set alarm state")
            self.update()
        else:
            _LOGGER.error("Failed to set alarm state, trying again")
            self.api.set_state(state, False)

    def get_sensors(self):
        return self.sensors




