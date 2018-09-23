# 🚨 simplipy: A Python3, asyncio interface to the SimpliSafe API

[![Travis CI](https://travis-ci.org/w1ll1am23/simplipy.svg?branch=master)](https://travis-ci.org/w1ll1am23/simplipy)
[![PyPi](https://img.shields.io/pypi/v/simplipy.svg)](https://pypi.python.org/pypi/simplipy)
[![Version](https://img.shields.io/pypi/pyversions/simplipy.svg)](https://pypi.python.org/pypi/simplipy)
[![License](https://img.shields.io/pypi/l/simplipy.svg)](https://github.com/w1ll1am23/simplipy/blob/master/LICENSE)
[![Code Coverage](https://codecov.io/gh/w1ll1am23/simplipy/branch/master/graph/badge.svg)](https://codecov.io/gh/w1ll1am23/simplipy)
[![Maintainability](https://api.codeclimate.com/v1/badges/af60d65b69d416136fc9/maintainability)](https://codeclimate.com/github/bachya/py17track/maintainability)
[![Say Thanks](https://img.shields.io/badge/SayThanks-!-1EAEDB.svg)](https://saythanks.io/to/w1ll1am23)

`simplisafe-python` (hereafter referred to as `simplipy`) is a Python3,
asyncio-driven interface to the unofficial SimpliSafe API. With it, users can
get data on their system (including available sensors), set the system state,
and more.

**NOTE:** SimpliSafe has no official API; therefore, this library may stop
working at any time without warning.

**SPECIAL THANKS:** Original source was obtained from
https://github.com/greencoder/simplipy; thanks to greencoder
for all the hard work!

# PLEASE READ: Version 3.0.0 and Beyond

Version 3.0.0 of `simplipy` makes several breaking, but necessary
changes:

* Moves the underlying library from
  [Requests](http://docs.python-requests.org/en/master/) to
  [aiohttp](https://aiohttp.readthedocs.io/en/stable/)
* Changes the entire library to use `asyncio`
* Makes 3.5 the minimum version of Python required

If you wish to continue using the previous, synchronous version of
`simplipy`, make sure to pin version 2.0.2.


# Installation

```python
pip install simplipy
```

# Usage

## Getting Systems Associated with An Account

`simplipy` starts within an
[aiohttp](https://aiohttp.readthedocs.io/en/stable/) `ClientSession`:

```python
import asyncio

from aiohttp import ClientSession


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
      # YOUR CODE HERE


asyncio.get_event_loop().run_until_complete(main())
```

To get all SimpliSafe systems associated with an email address:

```python
import asyncio

from aiohttp import ClientSession

from simplipy import get_systems


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
      systems = await get_systems("<EMAIL>", "<PASSWORD>", websession)
      # >>> [simplipy.system.SystemV2, simplipy.system.SystemV3]

asyncio.get_event_loop().run_until_complete(main())
```

## The `System` Object

`System` objects are used to retrieve data on and control the state
of SimpliSafe systems. Two types of objects can be returned:

* `SystemV2`: an object to control V2 (classic) SimpliSafe systems
* `SystemV3`: an object to control V3 (new, released in 2018) SimpliSafe systems

Despite the differences, `simplipy` provides a common interface to
these objects, meaning the same properties and methods are available to both.

### Properties and Methods

```python
from simplypy import get_systems

systems = await get_systems("<EMAIL>", "<PASSWORD>", websession)
# >>> [simplipy.system.SystemV2]

for system in systems:
  # Return a reference to a SimpliSafe account object (detailed later):
  primary_system.account
  # >>> simplipy.account.SimpliSafe

  # Return whether the alarm is currently going off:
  primary_system.alarm_going_off
  # >>> False

  # Return a list of sensors attached to this sytem:
  primary_system.sensors
  # >>> [simplipy.sensor.SensorV2, simplipy.sensor.SensorV2, ...]

  # Return the system's serial number:
  primary_system.serial
  # >>> 1234ABCD

  # Return the current state of the system:
  primary_system.state
  # >>> simplipy.system.SystemStates.away

  # Return the SimpliSafe identifier for this system:
  primary_system.system_id
  # >>> 1234ABCD

  # Return the SimpliSafe version:
  primary_system.version
  # >>> 2

  # Return a list of events for the system with an optional start timestamp and
  # number of events - omitting these parameters will return all events (max of
  # 50) stored in SimpliSafe's cloud:
  await primary_system.get_events(from_timestamp=1534035861, num_events=2)
  # >>> return {"numEvents": 2, "lastEventTimestamp": 1534035861, "events": [{...}]}

  # Set the state of the system:
  await primary_system.set_away()
  await primary_system.set_home()
  await primary_system.set_off()

  # Get the latest values from the system; by default, include both system info
  # and sensor info and use cached values (both can be overridden):
  await primary_system.update(refresh_location=True, cached=True)
```

### A Note on `system.update()`

There is one crucial difference between V2 and V3 systems when updating:

* V2 systems, which use only 2G cell connectivity, will be slower to update
  than V3 systems when those V3 systems are connected to WiFi.
* V2 systems will audibly announce, "Your settings have been synchronized."
  when the update completes; V3 systems will not. Unfortunately, this cannot
  currently be worked around.

## The `Sensor` Object

`Sensor` objects provide information about the SimpliSafe sensor to
which they relate.

**NOTE:** Individual sensors cannot be updated directly; instead,
the `update()` method on their parent `System` object should be used. It is
crucial to remember that sensor values are only as current as the last time
`system.update()` was called.

Like their `System` cousins, two types of objects can be returned:

* `SensorV2`: an object to view V2 (classic) SimpliSafe sensors
* `SensorV3`: an object to view V3 (new) SimpliSafe sensors

Once again, `simplipy` provides a common interface to
these objects; however, there are some properties that are either (a) specific
to one version or (b) return a different meaning based on the version. These
differences are outlined below.

### Base Properties

```python
from simplypy import get_systems

systems = await get_systems("<EMAIL>", "<PASSWORD>", websession)
for system in systems:
  for sensor in system.sensors:
    # Return the sensor's name:
    sensor.name
    # >>> Kitchen Window

    # Return the sensor's serial number:
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

    # Return whether the sensor has been triggered:
    sensor.triggered
    # >>> False
```

### V2 Properties

```python
from simplypy import get_systems

systems = await get_systems("<EMAIL>", "<PASSWORD>", websession)
for system in systems:
  for sensor in system.sensors:
    # Return the sensor's data as a currently non-understood integer:
    sensor.data
    # >>> 0

    # Return the sensor's settings as a currently non-understood integer:
    sensor.settings
    # >>> 1
```

### V3 Properties

```python
from simplypy import get_systems

systems = await get_systems("<EMAIL>", "<PASSWORD>", websession)
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
```

## The `Account` Object

Each `System` object has a reference to an `Account` object. This object
contains properties and a method useful for authentication and account
access.

**VERY IMPORTANT NOTE:** the `Account` object contains references to
SimpliSafe access and refresh tokens. **It is vitally important that you do
not let these tokens leave your control.** If exposed, savvy attackers could
use them to view and alter your system's state. **You have been warned; proper
usage of these properties is solely your responsibility.**

```python
systems = await get_systems("<EMAIL>", "<PASSWORD>", websession)
for system in systems:
  # Return the current access token:
  system.account.access_token
  # >>> 7s9yasdh9aeu21211add

  # Return the current refresh token:
  system.account.refresh_token
  # >>> 896sad86gudas87d6asd

  # Return the SimpliSafe user ID associated with this account:
  system.account.user_id
  # >>> 1234567
```

# Errors/Exceptions

`simplipy` exposes three useful error types:

* `simplipy.errors.SimplipyError`: a base error that all other `simplipy`
  errors inherit from
* `simplipy.errors.RequestError`: an error related to HTTP requests that return
  something other than a `200` response code
* `simplipy.errors.TokenExpiredError`: an error related to an expired access
  token

# Access and Refresh Tokens

When `simplipy.get_systems()` is run, everything is set to make repeated
authorized requests against the SimpliSafe cloud. At some point, however, the
access token will expire and any future requests will raise
`simplipy.errors.TokenExpiredError`.

When this occurs, a new access token can easily be generated:

```python
await system.account.refresh_access_token()
```

This will use the "on-file" refresh token to request a new access token; once
the call is complete, you're good to go.

In some instances, it may be desirable to store the "on-file" refresh token for
later use (for example, if your app/script/etc. stops and needs to restart at
some indeterminate point in the future). In that case, the
`refresh_access_token()` method can take an optional `refresh_token` parameter:

```python
await system.account.refresh_access_token(refresh_token='abcdefg987665')
```

Although no official documentation exists, basic testing appears to confirm the
hypothesis that the refresh token is both long-lived and single-use. This means
that theoretically, it should be possible to use it to create an access token
long into the future. If `refresh_access_token()` should throw an error,
however, the system object(s) will need to be recreated via
`simplipy.get_systems`.
