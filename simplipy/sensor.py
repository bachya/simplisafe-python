"""
SimpliSafe sensor object.
"""
import logging

_LOGGER = logging.getLogger(__name__)

SYSTEM_TYPE_MAP = {1: "keypad", 2: "keychain", 3: "panic button",
                   4: "motion", 5: "entry", 6: "glass break",
                   7: "carbon monoxide", 8: "smoke", 9: "leak",
                   10: "temperature"}


class SimpliSafeSensor(object):
    """
    Represents a SimpliSafe sensor.
    """

    def __init__(self, api_interface, sensor_dict, version):
        """
        Sensor object.

        Args:
            api_interfce (object): The API object to handle communication
                                   to and from the API.
            sensor_dict (dict): The sensor's current state.
        """
        self.sensor_dict = sensor_dict
        _type = sensor_dict["type"]
        if _type in SYSTEM_TYPE_MAP.keys():
            self.type = SYSTEM_TYPE_MAP[_type]
        else:
            _LOGGER.error("Invalid sensor type, please report this")
        self.version = version
        self.api_interface = api_interface

    def status(self):
        """Return the current sensor status."""
        if self.version != 3:
            return self.sensor_dict["sensorStatus"]
        if self.type == "temperature":
            return self._get_dict_values(["status", "temperature"], None)
        elif self.sensor_dict["type"] in [4, 5, 7, 8, 9]:
            return self._get_dict_values(["status", "triggered"], None)
        _LOGGER.debug(str(self.sensor_dict))
        return None

    def battery(self):
        """Return the battery status of the sensor."""
        if self.version != 3:
            return self.sensor_dict.get("battery") == "ok"
        return self._get_dict_values(["flags", "lowBattery"], False)

    def data(self):
        """Return the current sensor data."""
        if self.version != 3:
            return self.sensor_dict["sensorData"]
        # V3 seems to abstract this data better so they don't send it?
        return None

    def error(self):
        """Return error status."""
        if self.version != 3:
            return self.sensor_dict["error"]
        return self._get_dict_values(["status", "malfunction"], False)

    def offline(self):
        """Return if the sensor is offline."""
        if self.version != 3:
            return False
        return self._get_dict_values(["flags", "offline"], False)

    def name(self):
        """Return the sensor's name."""
        return self.sensor_dict["name"]

    def serial(self):
        """Return the sensor's serial number."""
        return self.sensor_dict["serial"]

    def _get_dict_values(self, path, return_on_err):
        current_dict = self.sensor_dict
        for node in path:
            if node in current_dict:
                current_dict = current_dict[node]
            else:
                return return_on_err
        return current_dict
