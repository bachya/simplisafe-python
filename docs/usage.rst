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

SimpliSafe™ offers several `monitoring plans <https://support.simplisafe.com/hc/en-us/articles/360023809972-What-are-the-service-plan-options->`_. Only the **Standard** and **Interactive** plans work with this library.


Please note that only Interactive plans can access sensor values and set the
system state; using the API with a Standard plan will be limited to retrieving
the current system state.

Accessing the API
-----------------

First, authenticate using your SimpliSafe username/email and password:

.. code:: python

    import asyncio

    from aiohttp import ClientSession
    import simplipy


    async def main() -> None:
        """Create the aiohttp session and run."""
        async with ClientSession() as session:
            api = await simplipy.API.async_from_credentials(
                "<USERNAME>"
                "<PASSWORD>"
                session=session,
            )


    asyncio.run(main())


This will create an object that is in a "pending" state, meaning that it now awaits
two-factor authentication. You can find the type of two-factor authentication by looking
at the ``auth_state`` property:

.. code:: python

    # If your account uses email-based two-factor authentication:
    api.auth_state
    # >>> simplipy.api.AuthStates.PENDING_2FA_EMAIL 

    # If your account uses SMS-based two-factor authentication:
    api.auth_state
    # >>> simplipy.api.AuthStates.PENDING_2FA_SMS 

Performing Email-Based Two-Factor Authentication
*************************************************

This type of two-factor authentication requires you to click a link in an email from
SimpliSafe. At any point, you can see if two-factor authentication has been completed:

.. code:: python

    api.async_verify_2fa_email()

If the two-factor authentication hasn't succeeded yet, ``simplipy`` will raise a
:meth:`Verify2FAPending  <simplipy.errors.Verify2FAPending>` exception. If it has
succeeded, the :meth:`API  <simplipy.api.API>` object is ready to use.

A common pattern in this scenario would be to loop and regularly test for authentication
(eventually timing out as appropriate):

.. code:: python

   try:
      async with timeout(30):
         try:
            await api.async_verify_2fa_email()
         except Verify2FAPending as err:
            print("Authentication not yet completed")
            await asyncio.sleep(3)
   except asyncio.TimeoutError as err:
      print("Timed out waiting for authentication")

   # Ready to use!

Performing SMS-Based Two-Factor Authentication
**********************************************

This type of two-factor authentication requires you to input a code received via SMS.
SimpliSafe. After you receive the code, you use it like this:

.. code:: python

    api.async_verify_2fa_sms("<CODE>")

If the two-factor authentication hasn't succeeded yet, ``simplipy`` will raise a
:meth:`InvalidCredentialsError  <simplipy.errors.InvalidCredentialsError>` exception.
If it has succeeded, the :meth:`API  <simplipy.api.API>` object is ready to use.

.. code:: python

   try:
      await api.async_verify_2fa_sms("<CODE>")
   except InvalidCredentialsError as err:
      print("Invalid SMS 2FA code")

   # Ready to use!

Key API Object Properties
*************************

The :meth:`API <simplipy.api.API>` object contains several sensitive properties to be
aware of:

.. code:: python

    # Return the current access token:
    api.access_token
    # >>> 7s9yasdh9aeu21211add

    # Return the current refresh token:
    api.refresh_token
    # >>> 896sad86gudas87d6asd

    # Return the SimpliSafe™ user ID associated with this account:
    api.user_id
    # >>> 1234567

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
            api = await simplipy.API.async_from_refresh_token(
                "<REFRESH_TOKEN>"
                session=session,
            )

            # ...


    asyncio.run(main())

The common practice is to store ``api.refresh_token`` somewhere (a filesystem, a
database, etc.), retrieve it later when needed, and pass it to
:meth:`async_from_refresh_token <simplipy.api.API.async_from_refresh_token>`. Be aware
that refresh tokens can only be used once!

After a new :meth:`API <simplipy.api.API>` object is created via 
:meth:`async_from_refresh_token <simplipy.api.API.async_from_refresh_token>`, it comes
with its own, new refresh token; this can be used to follow the same re-authentication
process into perpetuity.

Note that you do not need to worry about refreshing the access token within an
:meth:`API <simplipy.api.API>` object's normal operations (if, for instance, you have an
application that runs for longer than an access token's lifespan); that is handled for
you transparently.

**VERY IMPORTANT NOTE: It is vitally important that you do not let these tokens leave
your control.** If exposed, savvy attackers could use them to view and alter your
system's state. **You have been warned; proper usage of these properties is solely your
responsibility.**
