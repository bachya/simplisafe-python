# simplisafe-python
Python3 interface to the SimpliSafe API.

Original source was obtained from https://github.com/greencoder/simplisafe-python

greencoder, thanks for all the hard work!

**NOTE** SimpliSafe has no official API therefore this library could stop working at any time, without warning.

```python
from simplipy.api import SimpliSafeApiInterface

simplisafe = SimpliSafeApiInterface("USERNAME", "PASSWORD")

for system in simplisafe.get_systems():
    print("Location ID: " + str(system.location_id))
    print("System version: " + str(system.version))
    print("System state: " + str(system.state))
    print("Alarming: " + str(system.alarm_active))
    print("Temperature: " + str(system.temperature))
    print("Sensors:")
    for sensor in system.get_sensors():
       print("\t" + sensor.name())
       print("\t\tType: " + str(sensor.type))
       print("\t\tSerial: " + str(sensor.serial()))
       print("\t\tData: " + str(sensor.data()))
       print("\t\tStatus: " + str(sensor.status()))
       print("\t\tBattery Ok: " + str(sensor.battery()))
       print("\t\tOffline: " + str(sensor.offline()))
       print("\t\tError: " + str(sensor.error()))
```
