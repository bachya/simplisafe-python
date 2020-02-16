Websocket
#########

**NOTE:** this feature is ``experimental``. It may (1) change its API without warning and
(2) stop working at any time.

``simplipy`` provides a websocket that allows for near-real-time detection of certain
events from a user's SimpliSafe™ system. This websocket can be accessed via the
``websocket`` property of the ``API`` object:

.. code:: python

    simplisafe = await simplipy.API.login_via_credentials(
        "<EMAIL>", "<PASSWORD>", websession
    )

    simplisafe.websocket
    # >>> <simplipy.websocket.Websocket object>

Connecting to the Websocket
---------------------------

.. code:: python

    await simplisafe.websocket.async_connect()

Disconnecting from the Websocket
--------------------------------

.. code:: python

    await simplisafe.websocket.async_disconnect()

Responding to Events
--------------------

Users respond to events by defining handlers (synchronous functions *or* coroutines) and
using the appropriate registration method. The following events exist:

* ``connect``: occurs when the websocket connection is established
* ``disconnect``: occurs when the websocket connection is terminated
* ``event``: occurs when any data is transmitted from the SimpliSafe™ cloud

Note that you can only register one handler (synchronous function or coroutine) per
event; calling ``async_on_<event>`` or ``on_<event>`` more than once will override the
existing handler (again, regardless of whether the old handler was a synchronous function
or a coroutine).

``connect``
***********

Asynchronous Connect Callback
=============================

.. code:: python

    async def async_connect_handler():
        print("I connected to the websocket")

    simplisafe.websocket.async_on_connect(async_connect_handler)

Synchronous Connect Callback
============================

.. code:: python

    def connect_handler():
        print("I connected to the websocket")

    simplisafe.websocket.on_connect(connect_handler)

``disconnect``
**************

Asynchronous Disconnect Callback
================================

.. code:: python

    async def async_disconnect_handler():
        print("I disconnected from the websocket")

    simplisafe.websocket.async_on_disconnect(async_disconnect_handler)

Synchronous Disconnect Callback
===============================

.. code:: python

    def disconnect_handler():
        print("I disconnected from the websocket")

    simplisafe.websocket.on_disconnect(disconnect_handler)

``event``
*********

Asynchronous Event Callback
===========================

.. code:: python

    async def async_event_handler(message):
        print(f"SimpliSafe websocket message: {message}")

    simplisafe.websocket.async_on_event(async_event_handler)

Synchronous Event Callback
==========================

.. code:: python

    def event_handler(message):
        print(f"SimpliSafe websocket message: {message}")

    simplisafe.websocket.on_event(event_handler)

Response Format
===============

The ``message`` argument will be a :ref:`message object <message:Messages>`:


.. code:: python

    print(message)
    # >>> Message(event='alarm_canceled', message="The system was disarmed" ...)


...and the ``event`` property of that object will be one of the following:

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
* ``entry_detected``
* ``home_exit_delay``
* ``lock_error``
* ``lock_locked``
* ``lock_unlocked``
* ``motion_detected``
* ``power_outage``
* ``power_restored``
* ``sensor_not_responding``
* ``sensor_restored``

If you should come across an event type that the helper does not know about (and see
a logger warning about it), please open an issue at
https://github.com/bachya/simplisafe-python/issues.
