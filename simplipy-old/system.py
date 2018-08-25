"""
SimpliSafe Alarm object.
"""
import logging

from simplipy.sensor import SimpliSafeSensor


_LOGGER = logging.getLogger(__name__)


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
                self.sensors.append(SimpliSafeSensor(api_interface, sensor, system_dict["version"]))

    def update(self):
        """
        Fetch all of the latest states from the API.
        """
        if self.api.get_subscriptions():
            response = self.api.get_system_state(self.location_id)
            if response:
                self.state = response["alarmState"]
                self.alarm_active = response["isAlarming"]
                self.temperature = response["temperature"]
            else:
                _LOGGER.error("Empty system state, failed to update.")
        else:
            _LOGGER.error("Failed to get update.")

    def set_state(self, state, retry=True):
        """
        Set the state of the alarm system.
        """
        if self.api.set_system_state(self.location_id, state):
            _LOGGER.debug("Successfuly set alarm state")
            self.update()
        else:
            if retry:
                _LOGGER.error("Failed to set alarm state, trying again")
                self.set_state(state, False)
            else:
                _LOGGER.error("Failed to set alarm state after retry")

    def get_sensors(self):
        return self.sensors
