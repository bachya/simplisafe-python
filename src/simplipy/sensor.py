"""
SimpliSafe sensor object.
"""
import logging

_LOGGER = logging.getLogger(__name__)

# What is a 3?
SYSTEM_TYPE_MAP = {1: "keypad", 2: "keychain", 4: "motion", 5: "open", 6: "glass break"}


class SimpliSafeSensor(object):
    """
    Represents a SimpliSafe sensor.
    """

    def __init__(self, api_interface, sensor_dict):
        """
        Sensor object.

        Args:
            api_interfce (object): The API object to handle communication
                                   to and from the API.
            sensor_dict (dict): The sensor's current state.
        """
        _type = sensor_dict["type"]
        if _type in SYSTEM_TYPE_MAP.keys():
            self.type = SYSTEM_TYPE_MAP[_type]
        else:
            _LOGGER.error("Invalid sensor type, please report this")
        self.battery = sensor_dict.get("battery")
        self.serial = sensor_dict["serial"]
        self.name = sensor_dict["name"]
        self.status = sensor_dict["sensorStatus"]
        self.data = sensor_dict["sensorData"]
        self.error = sensor_dict["error"]
        self.entry_status = sensor_dict.get("entryStatus")

    def status(self):
        """Return the current sensor status."""
        return self.status

    def data(self):
        """Return the current sensor data."""
        return self.data

    def name(self):
        """Return the sensor's name."""
        return self.name

    def serial(self):
        """Return the sensor's serial number."""
        return self.serial
