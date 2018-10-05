# 🚨 simplisafe-python: A Python3, async interface to the SimpliSafe™ API

[![Travis CI](https://travis-ci.org/bachya/simplisafe-python.svg?branch=master)](https://travis-ci.org/bachya/simplisafe-python)
[![PyPi](https://img.shields.io/pypi/v/simplisafe-python.svg)](https://pypi.python.org/pypi/simplisafe-python)
[![Version](https://img.shields.io/pypi/pyversions/simplisafe-python.svg)](https://pypi.python.org/pypi/simplisafe-python)
[![License](https://img.shields.io/pypi/l/simplisafe-python.svg)](https://github.com/bachya/simplisafe-python/blob/master/LICENSE)
[![Code Coverage](https://codecov.io/gh/bachya/simplisafe-python/branch/master/graph/badge.svg)](https://codecov.io/gh/bachya/simplisafe-python)
[![Maintainability](https://api.codeclimate.com/v1/badges/f46d8b1dcfde6a2f683d/maintainability)](https://codeclimate.com/github/bachya/simplisafe-python/maintainability)
[![Say Thanks](https://img.shields.io/badge/SayThanks-!-1EAEDB.svg)](https://saythanks.io/to/bachya)

`simplisafe-python` (hereafter referred to as `simplipy`) is a Python3,
`asyncio`-driven interface to the unofficial SimpliSafe™ API. With it, users can
get data on their system (including available sensors), set the system state,
and more.

**NOTE:** SimpliSafe™ has no official API; therefore, this library may stop
working at any time without warning.

**SPECIAL THANKS:** Original inspiration was obtained from
https://github.com/greencoder/simplipy; thanks to Scott Newman for all the
hard work!

# PLEASE READ: Version 3.0.0 and Beyond

Version 3.0.0 of `simplipy` makes several breaking, but necessary
changes:

* Moves the underlying library from
  [Requests](http://docs.python-requests.org/en/master/) to
  [aiohttp](https://aiohttp.readthedocs.io/en/stable/)
* Changes the entire library to use `asyncio`
* Makes 3.6 the minimum version of Python required

If you wish to continue using the previous, synchronous version of
`simplipy`, make sure to pin version 2.0.2.

# Versions

`simplisafe-python` is currently supported on:

* Python 3.5
* Python 3.6
* Python 3.7

However, running the test suite currently requires Python 3.6 or higher; tests
run on Python 3.5 will fail.

# Installation

```python
pip install simplisafe-python
```

# Usage

## Getting Systems Associated with an Account

`simplipy` starts within an
[aiohttp](https://aiohttp.readthedocs.io/en/stable/) `ClientSession`:

```python
import asyncio

from aiohttp import ClientSession


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      # YOUR CODE HERE


asyncio.get_event_loop().run_until_complete(main())
```

To get all SimpliSafe™ systems associated with an account:

```python
import asyncio

from aiohttp import ClientSession

from simplipy import API


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      simplisafe = API.login_via_credentials("<EMAIL>", "<PASSWORD>", websession)
      systems = await simplisafe.get_systems()
      # >>> [<simplipy.system.SystemV2 object at 0x10661e3c8>, ...]


asyncio.get_event_loop().run_until_complete(main())
```

## The `System` Object

`System` objects are used to retrieve data on and control the state
of SimpliSafe™ systems. Two types of objects can be returned:

* `SystemV2`: an object to control V2 (classic) SimpliSafe™ systems
* `SystemV3`: an object to control V3 (new, released in 2018) SimpliSafe™ systems

Despite the differences, `simplipy` provides a common interface to
these objects, meaning the same properties and methods are available to both.

### Properties and Methods

```python
from simplipy import API


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      simplisafe = API.login_via_credentials("<EMAIL>", "<PASSWORD>", websession)
      systems = await simplisafe.get_systems()
      # >>> [<simplipy.system.SystemV2 object at 0x10661e3c8>]

      for system in systems:
        # Return a reference to a SimpliSafe™ API object (detailed later):
        system.api
        # >>> <simplipy.api.API object at 0x12aba2321>

        # Return the street address of the system:
        system.address
        # >>> 1234 Main Street

        # Return whether the alarm is currently going off:
        system.alarm_going_off
        # >>> False

        # Return a list of sensors attached to this sytem (detailed later):
        system.sensors
        # >>> [<simplipy.sensor.SensorV2 object at 0x10661e3c8>, ...]

        # Return the system's serial number:
        system.serial
        # >>> 1234ABCD

        # Return the current state of the system:
        system.state
        # >>> simplipy.system.SystemStates.away

        # Return the SimpliSafe™ identifier for this system:
        system.system_id
        # >>> 1234ABCD

        # Return the average of all temperature sensors (if they exist):
        system.temperature
        # >>> 67

        # Return the SimpliSafe™ version:
        system.version
        # >>> 2

        # Return a list of events for the system with an optional start timestamp and
        # number of events - omitting these parameters will return all events (max of
        # 50) stored in SimpliSafe™'s cloud:
        await system.get_events(from_timestamp=1534035861, num_events=2)
        # >>> return {"numEvents": 2, "lastEventTimestamp": 1534035861, "events": [{...}]}

        # Set the state of the system:
        await system.set_away()
        await system.set_home()
        await system.set_off()

        # Get the latest values from the system; by default, include a refresh
        # of system info and use cached values (both can be overridden):
        await system.update(refresh_location=True, cached=True)


asyncio.get_event_loop().run_until_complete(main())
```

### A Note on `system.update()`

There are two crucial differences between V2 and V3 systems when updating:

* V2 systems, which use only 2G cell connectivity, will be slower to update
  than V3 systems when those V3 systems are connected to WiFi.
* V2 systems will audibly announce, "Your settings have been synchronized."
  when the update completes; V3 systems will not. Unfortunately, this cannot
  currently be worked around.

## The `Sensor` Object

`Sensor` objects provide information about the SimpliSafe™ sensors to
which they relate.

**NOTE:** Individual sensors cannot be updated directly; instead,
the `update()` method on their parent `System` object should be used. It is
crucial to remember that sensor values are only as current as the last time
`system.update()` was called.

Like their `System` cousins, two types of objects can be returned:

* `SensorV2`: an object to view V2 (classic) SimpliSafe™ sensors
* `SensorV3`: an object to view V3 (new, released in 2018) SimpliSafe™ sensors

Once again, `simplipy` provides a common interface to
these objects; however, there are some properties that are either (a) specific
to one version or (b) return a different meaning based on the version. These
differences are outlined below.

### Base Properties

```python
from simplipy import API


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      simplisafe = API.login_via_credentials("<EMAIL>", "<PASSWORD>", websession)
      systems = await simplisafe.get_systems()
      for system in systems:
        for serial, sensor_attrs in system.sensors.items():
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
          # >>> simplipy.sensor.SensorTypes.glass_break

          # Return whether the sensor is in an error state:
          sensor.error
          # >>> False

          # Return whether the sensor has a low battery:
          sensor.low_battery
          # >>> False

          # Return whether the sensor has been triggered (open/closed, etc.):
          sensor.triggered
          # >>> False


asyncio.get_event_loop().run_until_complete(main())
```

### V2 Properties

```python
from simplipy import API


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      simplisafe = API.login_via_credentials("<EMAIL>", "<PASSWORD>", websession)
      systems = await simplisafe.get_systems()
      for system in systems:
        for serial, sensor_attrs in system.sensors.items():
          # Return the sensor's data as a currently non-understood integer:
          sensor.data
          # >>> 0

          # Return the sensor's settings as a currently non-understood integer:
          sensor.settings
          # >>> 1


asyncio.get_event_loop().run_until_complete(main())
```

### V3 Properties

```python
from simplipy import API


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      simplisafe = API.login_via_credentials("<EMAIL>", "<PASSWORD>", websession)
      systems = await simplisafe.get_systems()
      for system in systems:
        for sensor in system.sensors:
          # Return whether the sensor is offline:
          sensor.offline
          # >>> False

          # Return a settings dictionary for the sensor:
          sensor.settings
          # >>> {"instantTrigger": False, "away2": 1, "away": 1, ...}

          # For temperature sensors, return the current temperature:
          sensor.temperature
          # >>> 67


asyncio.get_event_loop().run_until_complete(main())
```

## The `API` Object

Each `System` object has a reference to an `API` object. This object contains
properties and a method useful for authentication and ongoing access.

**VERY IMPORTANT NOTE:** the `API` object contains references to
SimpliSafe™ access and refresh tokens. **It is vitally important that you do
not let these tokens leave your control.** If exposed, savvy attackers could
use them to view and alter your system's state. **You have been warned; proper
usage of these properties is solely your responsibility.**

```python
from simplipy import API


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      simplisafe = API.login_via_credentials("<EMAIL>", "<PASSWORD>", websession)
      systems = await simplisafe.get_systems()
      for system in systems:
        # Return the current access token:
        system.api._access_token
        # >>> 7s9yasdh9aeu21211add

        # Return the current refresh token:
        system.api.refresh_token
        # >>> 896sad86gudas87d6asd

        # Return the SimpliSafe™ user ID associated with this account:
        system.api.user_id
        # >>> 1234567


asyncio.get_event_loop().run_until_complete(main())
```

# Errors/Exceptions

`simplipy` exposes two useful error types:

* `simplipy.errors.SimplipyError`: a base error that all other `simplipy`
  errors inherit from
* `simplipy.errors.RequestError`: an error related to HTTP requests that return
  something other than a `200` response code

# Refreshing the Access Token

## General Notes

During usage, `simplipy` will automatically refresh the access token as needed.
At any point, the "dirtiness" of the token can be checked:

```python
from simplipy import API


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      simplisafe = API.login_via_token("<REFRESH TOKEN>", websession)
      systems = await simplisafe.get_systems()
      primary_system = systems[0]

      # Assuming the access token was automatically refreshed:
      primary_system.api.refresh_token_dirty
      # >>> True

      # Once the dirtiness is confirmed, the dirty bit resets:
      primary_system.api.refresh_token_dirty
      # >>> False


asyncio.get_event_loop().run_until_complete(main())
```

## Restarting with a Refresh Token

It may be desirable to re-authenticate against the SimpliSafe™ API at some
point in the future (and without using a user's email and password). In that
case, it is recommended that you save the `refresh_token` property somewhere;
when it comes time to re-authenticate, simply:

```python
from simplipy import API


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as websession:
      simplisafe = API.login_via_token("<REFRESH TOKEN>", websession)
      systems = await simplisafe.get_systems()
      # ...


asyncio.get_event_loop().run_until_complete(main())
```

Although no official documentation exists, basic testing appears to confirm the
hypothesis that the refresh token is both long-lived and single-use. This means
that theoretically, it should be possible to use it to create an access token
long into the future. If `login_via_token()` should throw an error, however,
the system object(s) will need to be recreated via `login_via_credentials()`.

# Contributing

1. [Check for open features/bugs](https://github.com/bachya/simplisafe-python/issues)
  or [initiate a discussion on one](https://github.com/bachya/simplisafe-python/issues/new).
2. [Fork the repository](https://github.com/bachya/simplisafe-python/fork).
3. Install the dev environment: `make init`.
4. Enter the virtual environment: `pipenv shell`
5. Code your new feature or bug fix.
6. Write a test that covers your new functionality.
7. Update `README.md` with any new documentation.
8. Run tests and ensure 100% code coverage: `make coverage`
9. Ensure you have no linting errors: `make lint`
10. Ensure you have no typed your code correctly: `make typing`
11. Add yourself to `AUTHORS.md`.
12. Submit a pull request!
