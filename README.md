# simplisafe-python
Python3 interface to the SimpliSafe API.

Original source was obtained from https://github.com/greencoder/simplisafe-python

greencoder, thanks for all the hard work!

**NOTE** SimpliSafe has no official API therefore this library could stop working at any time, without warning.

```python
from simplipy.api import SimpliSafeApiInterface

simplisafe = SimpliSafeApiInterface("USERNAME", "PASSWORD")


for system in simplisafe.get_systems():
    print(system.state)
    print(str(simplisafe.sensors))
    for sensor in system.get_sensors():
        print(sensor.name)
        print("\t" + str(sensor.status))
```
