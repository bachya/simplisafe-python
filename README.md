# 🚨 simplisafe-python: A Python3, asyncio interface to the SimpliSafe API

[![Travis CI](https://travis-ci.org/w1ll1am23/simplisafe-python.svg?branch=master)](https://travis-ci.org/w1ll1am23/simplisafe-python)
[![PyPi](https://img.shields.io/pypi/v/simplisafe-python.svg)](https://pypi.python.org/pypi/simplisafe-python)
[![Version](https://img.shields.io/pypi/pyversions/simplisafe-python.svg)](https://pypi.python.org/pypi/simplisafe-python)
[![License](https://img.shields.io/pypi/l/simplisafe-python.svg)](https://github.com/w1ll1am23/simplisafe-python/blob/master/LICENSE)
[![Code Coverage](https://codecov.io/gh/w1ll1am23/simplisafe-python/branch/master/graph/badge.svg)](https://codecov.io/gh/w1ll1am23/simplisafe-python)
[![Maintainability](https://api.codeclimate.com/v1/badges/af60d65b69d416136fc9/maintainability)](https://codeclimate.com/github/bachya/py17track/maintainability)
[![Say Thanks](https://img.shields.io/badge/SayThanks-!-1EAEDB.svg)](https://saythanks.io/to/w1ll1am23)

`simplisafe-python` (more simply referred to as `simplipy`) is a Python3,
asyncio-driven interface to the unofficial SimpliSafe API. With it, users can
get data on their system (including available sensors), set the system state,
and more.

**NOTE:** SimpliSafe has no official API; therefore, this library may stop
working at any time without warning.

**SPECIAL THANKS:** Original source was obtained from
https://github.com/greencoder/simplisafe-python; thanks to greencoder
for all the hard work!

# PLEASE READ: Version 3.0.0 and Beyond

Version 3.0.0 of `simplisafe-python` makes several breaking, but necessary
changes:

* Moves the underlying library from
  [Requests](http://docs.python-requests.org/en/master/) to
  [aiohttp](https://aiohttp.readthedocs.io/en/stable/)
* Changes the entire library to use `asyncio`
* Makes 3.5 the minimum version of Python required

If you wish to continue using the previous, synchronous version of
`simplisafe-python`, make sure to pin version 2.0.2.


# Installation

```python
pip install simplisafe-python
```

# Usage: Getting Systems

`simplisafe-python` starts within an
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

Then, get all SimpliSafe systems associated with an email address:

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

# Usage: SimpliSafe System Object

`simplipy.get_systems` returns a list of SimpliSafe `System` objects. Two types
of objects can be created:

* `SystemV2`: an object to control V2 (classic) SimpliSafe systems
* `SystemV3`: an object to control V3 (new) SimpliSafe systems

Although all systems have a common base interface, there are differences
between V2 and V3.

## Base Properties and Methods

```python
systems = await get_systems("<EMAIL>", "<PASSWORD>", websession)
# >>> [simplipy.system.SystemV2]

primary_system = systems[0]

# Return whether the alarm is going off:
primary_system.alarm_going_off

# Return the system's serial number:
primary_system.serial

# Return the current state of the system:
primary_system.state
# >>> simplipy.system.SystemStates.away

# Return the SimpliSafe identifier for this system:
primary_system.system_id

# Return the SimpliSafe version:
primary_system.version
```

## V2 Properties and Methods
