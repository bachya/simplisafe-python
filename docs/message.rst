Messages
========

At various times (most notably when dealing with
:ref:`websocket events <websocket:Responding to Events>` and system notifications),
``simplipy`` will make use of :meth:`simplipy.helpers.message.Message` objects. These
objects provide an easy-to-use interface for this data, rather than dealing with raw,
sometimes difficult-to-decipher data directly from SimpliSafe™.

Each object has the following properties:

* ``changed_by``: In cases of messages about system arm/disarm events, the PIN that caused the message
* ``event``: The event that caused the message (e.g., ``lock_unlocked``)
* ``message``: The message text
* ``sensor_name``: The sensor name that caused the message (if appropriate)
* ``sensor_serial``: The sensor serial number that caused the message (if appropriate)
* ``sensor_type``: The sensor type that caused the message (if appropriate)
* ``system_id``: The system ID for which the message applies
* ``timestamp``: The UTC ``datetime`` that the message was generated
