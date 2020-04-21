Usage
=====


Installation
------------

.. code:: bash

   pip install simplisafe-python

Python Versions
---------------

``simplisafe-python`` is currently supported on:

* Python 3.7
* Python 3.8

SimpliSafe Plans
----------------

SimpliSafe™ offers two different monitoring plans:

    **Standard:** Monitoring specialists guard your home around-the-clock from
    our award-winning monitoring centers. In an emergency, we send the police to
    your home. Free cellular connection built-in.

    **Interactive:** Standard + advanced mobile app control of your system from
    anywhere in the world. Get text + email alerts, monitor home activity,
    arm/disarm your system, control settings right on your smartphone or laptop.
    Bonus: Secret! Alerts—get secretly notified when anyone accesses private
    rooms, drawers, safes and more.

Please note that only Interactive plans can access sensor values and set the
system state; using the API with a Standard plan will be limited to retrieving
the current system state.

Connection Pooling
------------------

By default, the :meth:`API <simplipy.api.API>` object creates a new connection to
SimpliSafe™ with each coroutine. If you are calling a large number of coroutines (or
merely want to squeeze out every second of runtime savings possible), an
``aiohttp ClientSession`` can be supplied when logging into the API (via credentials or
token) to achieve connection pooling:

.. code:: python

    import asyncio

    from aiohttp import ClientSession
    import simplipy


    async def main() -> None:
        """Create the aiohttp session and run."""
        async with ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                "<EMAIL>", "<PASSWORD>", session=session
            )

            # ...


    asyncio.run(main())

Every example in this documentation uses this pattern.
