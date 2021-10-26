Usage
=====


Installation
------------

.. code:: bash

   pip install simplisafe-python

Python Versions
---------------

``simplisafe-python`` is currently supported on:

* Python 3.8
* Python 3.9
* Python 3.10

SimpliSafe™ Plans
-----------------

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

Starting in 2021, SimpliSafe™  began to implement an OAuth-based form of authentication.
To use this library, you must handshake with the SimpliSafe™  API; although this process
cannot be 100% accomplished programmatically, the procedure is fairly straightforward.

Authentication
**************

``simplipy`` comes with a helper script to get you started. To use it, follow these
steps from a command line:

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

4. Run the ``auth`` script:

.. code:: bash

    $ script/auth

5. This will open your browser to a SimpliSafe™ login page. Once you log in with your
   credentials, you will see a "Verification Pending" webpage (we'll call this
   ``Tab 1``):

.. image:: images/ss-login-screen.png
   :width: 400

6. Check your email; you should see an email from SimpliSafe™ asking you to verify the
   new authentication request:

.. image:: images/ss-verification-email.png
   :width: 400

7. Once you click the "Verify Device" link, a new browser tab (``Tab 2``) will open
   and notify you that the verification is successful:

.. image:: images/ss-verification-confirmed.png
   :width: 400

8. Return to ``Tab 1``. The browser will show an error about not being able to navigate
   to the page; ignore it. Instead, take a look at the URL and note the ``code``
   parameter at the very end:

.. code::

   com.simplisafe.mobile://auth.simplisafe.com/ios/com.simplisafe.mobile/callback?code=<CODE>

9. Copy the ``code`` parameter, return to your terminal, and paste it into the prompt.
   You should now see this message:

.. code::

   You are now ready to use the SimpliSafe API!
   Authorization Code: <CODE>
   Code Verifier: <VERIFIER>

These one-time values are now ready to be used to instantiate an
:meth:`API <simplipy.api.API>` object.

Creating an API Object
**********************

Once you have an Authorization Code and Code Verifier, you can create an API object like
this:

.. code:: python

    import asyncio

    from aiohttp import ClientSession
    import simplipy


    async def main() -> None:
        """Create the aiohttp session and run."""
        async with ClientSession() as session:
            simplisafe = await simplipy.API.async_from_auth(
                "<AUTHORIZATION_CODE>",
                "<CODE_VERIFIER>",
                session=session,
            )

            # ...


    asyncio.run(main())

**REMINDER:** this Authorization Code and Code Verifier can only be used once. 

Refreshing the Access Token
***************************

The official way to create an :meth:`API <simplipy.api.API>` object after the initial
Authorization Code/Code Verifier handshake is to use the refresh token to generate a new
access token:

.. code:: python

    import asyncio

    from aiohttp import ClientSession
    import simplipy


    async def main() -> None:
        """Create the aiohttp session and run."""
        async with ClientSession() as session:
            simplisafe = await simplipy.API.async_from_auth(
                "<AUTHORIZATION_CODE>",
                "<CODE_VERIFIER>",
                session=session,
            )

            # Sometime later:
            new_simplisafe = await simplipy.API.async_from_refresh_token(
                simplisafe.refresh_token,
                session=session,
            )

            # ...


    asyncio.run(main())

Note that you do not need to worry about refreshing the access token within an
:meth:`API <simplipy.api.API>` object's normal operations; that is handled for you. The
primary reason you would interface with the refresh token yourself is when you need to
create a new object (as above).
