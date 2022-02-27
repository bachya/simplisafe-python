Websocket
#########

``simplipy`` provides a websocket that allows for near-real-time detection of certain
events from a user's SimpliSafe™ system. This websocket can be accessed via the
``websocket`` property of the :meth:`API <simplipy.api.API>` object:

.. code:: python

    api.websocket
    # >>> <simplipy.websocket.Websocket object>

Connecting
----------

.. code:: python

    await api.websocket.async_connect()

Then, once you are connected to the websocket, you can start listening for events:

.. code:: python

    await api.websocket.async_listen()

Disconnecting
-------------

.. code:: python

    await api.websocket.async_disconnect()

Responding to Events
--------------------

Users respond to events by defining callbacks (synchronous functions *or* coroutines).
The following events exist:

* ``connect``: occurs when the websocket connection is established
* ``disconnect``: occurs when the websocket connection is terminated
* ``event``: occurs when any data is transmitted from the SimpliSafe™ cloud

Note that you can register as many callbacks as you'd like.

``connect``
***********

.. code:: python

    async def async_connect_handler():
        await asyncio.sleep(1)
        print("I connected to the websocket")

    def connect_handler():
        print("I connected to the websocket")

    remove_1 = api.websocket.add_connect_callback(async_connect_handler)
    remove_2 = api.websocket.add_connect_callback(connect_handler)

    # remove_1 and remove_2 are functions that, when called, remove the callback.

``disconnect``
**************

.. code:: python

    async def async_connect_handler():
        await asyncio.sleep(1)
        print("I disconnected from the websocket")

    def connect_handler():
        print("I disconnected from the websocket")

    remove_1 = api.websocket.add_disconnect_callback(async_connect_handler)
    remove_2 = api.websocket.add_disconnect_callback(connect_handler)

    # remove_1 and remove_2 are functions that, when called, remove the callback.

``event``
*********

.. code:: python

    async def async_connect_handler(event):
        await asyncio.sleep(1)
        print(f"I received a SimpliSafe™ event: {event}")

    def connect_handler():
        print(f"I received a SimpliSafe™ event: {event}")

    remove_1 = api.websocket.add_event_callback(async_connect_handler)
    remove_2 = api.websocket.add_event_callback(connect_handler)

    # remove_1 and remove_2 are functions that, when called, remove the callback.

Response Format
===============

The ``event`` argument provided to event callbacks is a
:meth:`simplipy.websocket.WebsocketEvent` object, which comes with several properties:

* ``changed_by``: the PIN that caused the event (in the case of arming/disarming/etc.)
* ``event_type``: the type of event (see below)
* ``info``: a longer string describing the event
* ``sensor_name``: the name of the entity that triggered the event
* ``sensor_serial``: the serial number of the entity that triggered the event
* ``sensor_type``: the type of the entity that triggered the event
* ``system_id``: the SimpliSafe™ system ID
* ``timestamp``: the UTC timestamp that the event occurred

The ``event_type`` property will be one of the following values:

* ``alarm_canceled``
* ``alarm_triggered``
* ``armed_away_by_keypad``
* ``armed_away_by_remote``
* ``armed_away``
* ``armed_home``
* ``automatic_test``
* ``away_exit_delay_by_keypad``
* ``away_exit_delay_by_remote``
* ``camera_motion_detected``
* ``connection_lost``
* ``connection_restored``
* ``disarmed_by_master_pin``
* ``disarmed_by_remote``
* ``doorbell_detected``
* ``entity_test``
* ``entry_detected``
* ``home_exit_delay``
* ``lock_error``
* ``lock_locked``
* ``lock_unlocked``
* ``motion_detected``
* ``power_outage``
* ``power_restored``
* ``sensor_not_responding``
* ``sensor_paired_and_named``
* ``sensor_restored``
* ``user_initiated_test``

If you should come across an event type that the library does not know about (and see
a log message about it), please open an issue at
https://github.com/bachya/simplisafe-python/issues.
