Sensors
=======

``Sensor`` objects provide information about the SimpliSafe™ sensors to
which they relate.

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

    # Return whether the sensor is offline:
    sensor.offline
    # >>> False

    # Return a settings dictionary for the sensor:
    sensor.settings
    # >>> {"instantTrigger": False, "away2": 1, "away": 1, ...}

    # For temperature sensors, return the current temperature:
    sensor.temperature
    # >>> 67

Updating the Sensor
-------------------

To retrieve the sensor's latest state/properties/etc., simply:

.. code:: python

    await sensor.update(cached=True)
