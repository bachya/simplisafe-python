Websocket
=========

**NOTE:** this feature is ``experimental`` and should be used with caution.

``simplipy`` provides a websocket that allows for near-real-time detection of certain
events from a user's SimpliSafe™ system. This websocket can be accessed via the
``websocket`` property of the ``API`` object:

.. code:: python

    simplisafe = await API.login_via_credentials(
        "<EMAIL>", "<PASSWORD>", websession
    )

    simplisafe.websocket
    # >>> <simplipy.websocket.Websocket object>

Responding to Events
--------------------

Users are currently able to subscribe to the following events:

* ``connect``: occurs when the websocket connection is established
* ``disconnect``: occurs when the websocket connection is terminated
* ``event``: occurs when any data is transmitted from the SimpliSafe™ cloud

Users respond to events by defining handlers (synchronous functions *or* coroutines) and
using the appropriate registration method.

``connect``
***********

For example, to register two handlers that should be executed when the websocket
connection is established:

.. code:: python

    def sync_connect_handler():
        print("Connected to the websocket")

    async def async_connect_handler():
        print("I also connected to the websocket")

    # Use the correct registration method: sync for sync, async
    # for async. Also note that each registration method can be
    # used for multiple handlers!
    simplisafe.websocket.async_on_connect(async_connect_handler)
    simplisafe.websocket.on_connect(sync_connect_handler)

``disconnect``
**************

.. code:: python

    def sync_disconnect_handler():
        print("Disconnected from the websocket")

    async def async_disconnect_handler():
        print("I also disconnected from the websocket")

    simplisafe.websocket.async_on_disconnect(async_disconnect_handler)
    simplisafe.websocket.on_disconnect(sync_disconnect_handler)

``event``
**************

.. code:: python

    def sync_event_handler(data):
        print(f"I got some data: {data}")

    async def async_event_handler():
        print(f"I also got some data: {data}")

    simplisafe.websocket.async_on_disconnect(async_event_handler)
    simplisafe.websocket.on_disconnect(sync_event_handler)

The data returned in the ``data`` argument has the same schema as data returned from
``system.get_events()``. For example, when the system is armed in home mode, users may
expect a ``data`` argument with this value:

.. code:: json

    {
      "eventId": 1231231231,
      "eventTimestamp": 1231231231,
      "eventCid": 1231,
      "zoneCid": "3",
      "sensorType": 0,
      "sensorSerial": "",
      "account": "xxxxxxxx",
      "userId": 123123,
      "sid": 123123,
      "info": "System Armed (Home) by Remote Management",
      "pinName": "",
      "sensorName": "",
      "messageSubject": "SimpliSafe System Armed (home mode)",
      "messageBody": "System Armed (home mode)",
      "eventType": "activity",
      "timezone": 2,
      "locationOffset": -420,
      "videoStartedBy": "",
      "video": {}
    }
