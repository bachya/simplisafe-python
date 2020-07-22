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

Accessing the API
-----------------

The usual way to create an API object is via the
:meth:`API.login_via_credentials <simplipy.api.API.login_via_credentials>` coroutine. In
order to use it effectively, you must first walk through SimpliSafe™'s multi-factor
authentication flow.

SimpliSafe™ Multi-Factor Authentication
***************************************

As of early 2020, SimpliSafe™ has begun to enforce a multi-factor authentication
mechanism in which any client accessing its private, unpublished API must first be
validated by the user.

``simplipy`` comes with a helper script that makes this process fairly painless. To use
it, follow these steps from a command line:

1. Clone the ``simplipy`` Git repo and ``cd`` into it:

.. code:: bash

    $ git clone https://github.com/bachya/simplisafe-python.git
    $ cd simplisafe-python/

2. Set up and activate a Python virtual environment:

.. code:: bash

    $ python3 -m virtualenv .venv
    $ source .venv/bin/activate

3. Initialize the dev environment for ``simplipy``:

.. code:: bash

    $ script/setup

4. Finally, run the ``mfa`` script:

.. code:: bash

    $ script/mfa

The script will ask for your SimpliSafe™ email address and password. After the process
completes, you should see a message like this:

.. code:: text

    Check your email for an MFA link, then use <UNIQUE IDENTIFIER> as the client_id
    parameter in future API calls

(Note that technically, the above message results from a
:meth:`PendingAuthorizationError <simplipy.errors.PendingAuthorizationError>`)
exception.)

5. Check your email. You should see an email from SimpliSafe™ asking you to verify a
   new device access – note that the User-Agent header shown in the email should include
   the unique identifier from the ``mfa`` script:

.. code:: text

    Someone tried to log in to your SimpliSafe account from a new device:

    Unknown App
    WebApp; useragent="Safari 13.1 (SS-ID: xxxxx-xxxxx) / macOS 10.15.6";
    uuid="<UNIQUE IDENTIFIER>"; id="xxxxx-xxxxx"
    IP address: 192.168.1.100

    We want to make sure that it's really you. Click below to verify this device.
    Link will expire in 15 minutes.

6. Click ``Verify Device`` in the email. This will allow the generated unique identifier
   future access to the API.

At this stage, you will be authorized to use the SimpliSafe™ API.

Creating an API Object
**********************

The primary way of creating an API object is via the
:meth:`API.login_via_credentials <simplipy.api.API.login_via_credentials>` coroutine:

.. code:: python

    import asyncio

    from aiohttp import ClientSession
    import simplipy


    async def main() -> None:
        """Create the aiohttp session and run."""
        async with ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                "<EMAIL>",
                "<PASSWORD>",
                client_id="<UNIQUE IDENTIFIER>",
                session=session,
            )

            # ...


    asyncio.run(main())

Note that the multi-factor authentication unique identifier is passed to the coroutine.

You can also use the
:meth:`API.login_via_token <simplipy.api.API.login_via_token>` coroutine, which is
detailed in :ref:`refreshing-access-tokens`.

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
                "<EMAIL>",
                "<PASSWORD>",
                client_id="<UNIQUE IDENTIFIER>",
                session=session,
            )

            # ...


    asyncio.run(main())

Every example in this documentation uses this pattern.
