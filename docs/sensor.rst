Sensors
=======

``Sensor`` objects provide information about the SimpliSafe™ sensors to
which they relate.

**NOTE:** Individual sensors cannot be updated directly; instead,
the ``update()`` method on their parent ``System`` object should be used. It is
crucial to remember that sensor states are only as current as the last time
``system.update()`` was called.

Like their ``System`` cousins, two types of objects can be returned:

* ``SensorV2``: an object to view V2 (classic) SimpliSafe™ sensors
* ``SensorV3``: an object to view V3 (new, released in 2018) SimpliSafe™ sensors

Once again, ``simplipy`` provides a common interface to
these objects; however, there are some properties that are either (a) specific
to one version or (b) return a different meaning based on the version. These
differences are outlined below.

Core Properties
---------------

All ``Sensor`` objects come with a standard set of properties

.. code:: python

    for serial, sensor in system.sensors.items():
        # Return the sensor's name:
        sensor.name
        # >>> Kitchen Window

        # Return the sensor's serial number through the index:
        serial
        # >>> 1234ABCD

        # ...or through the property:
        sensor.serial
        # >>> 1234ABCD

        # Return the sensor's type:
        sensor.type
        # >>> simplipy.EntityTypes.glass_break

        # Return whether the sensor is in an error state:
        sensor.error
        # >>> False

        # Return whether the sensor has a low battery:
        sensor.low_battery
        # >>> False

        # Return whether the sensor has been triggered
        # (open/closed, etc.):
        sensor.triggered
        # >>> False

V2 Properties
-------------

.. code:: python

    for serial, sensor in system.sensors.items():
        # Return the sensor's data as a currently
        # non-understood integer:
        sensor.data
        # >>> 0

        # Return the sensor's settings as a currently
        # non-understood integer:
        sensor.settings
        # >>> 1

V3 Properties
-------------

.. code:: python

    for serial, sensor in system.sensors.items():
        # Return whether the sensor is offline:
        sensor.offline
        # >>> False

        # Return a settings dictionary for the sensor:
        sensor.settings
        # >>> {"instantTrigger": False, "away2": 1, "away": 1, ...}

        # For temperature sensors, return the current temperature:
        sensor.temperature
        # >>> 67
