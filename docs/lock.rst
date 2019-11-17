Locks
=====

``Lock`` objects correspond to SimpliSafe™ locks (only available for V3 systems) and
allows users to retrieve information on them and alter their state by
locking/unlocking them.

**NOTE:** Individual locks cannot be updated directly; instead, the ``update()``
method on their parent ``System`` object should be used. It is crucial to remember
that lock states are only as current as the last time ``system.update()`` was
called. The only exception to this rule is when ``lock.lock()`` or
``lock.unlock()`` are called; both of these will automatically update the lock
state.

Core Properties
---------------

All ``Sensor`` objects come with a standard set of properties

.. code:: python

    for serial, lock in system.locks.items():
        # Return the lock's name:
        lock.name
        # >>> Kitchen Window

        # Return the lock's serial number through the index:
        serial
        # >>> 1234ABCD

        # ...or through the property:
        lock.serial
        # >>> 1234ABCD

        # Return the state of the lock:
        lock.state
        # >>> simplipy.lock.LockStates.locked

        # Return whether the lock is in an error state:
        lock.error
        # >>> False

        # Return whether the lock has a low battery:
        lock.low_battery
        # >>> False

        # Return whether the lock is offline:
        lock.offline
        # >>> False

        # Return a settings dictionary for the lock:
        lock.settings
        # >>> {"autoLock": 3, "away": 1, "home": 1}

        # Return whether the lock is disabled:
        lock.disabled
        # >>> False

        # Return whether the lock's battery is low:
        lock.lock_low_battery
        # >>> False

        # Return whether the pin pad's battery is low:
        lock.pin_pad_low_battery
        # >>> False

        # Return whether the pin pad is offline:
        lock.pin_pad_offline
        # >>> False

Locking/Unlocking
-----------------

Locking and unlocking a lock is accomplished via two coroutines:

.. code:: python

    for serial, lock in system.locks.items():
        await lock.lock()
        await lock.unlock()
