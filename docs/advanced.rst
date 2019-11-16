Advanced Usage
--------------

The API Object
**************

Each ``System`` object has a reference to an ``API`` object. This object contains
properties and a method useful for authentication and ongoing access.

**VERY IMPORTANT NOTE:** the ``API`` object contains references to
SimpliSafe™ access and refresh tokens. **It is vitally important that you do
not let these tokens leave your control.** If exposed, savvy attackers could
use them to view and alter your system's state. **You have been warned; proper
usage of these properties is solely your responsibility.**

.. code:: python

    # Return the current access token:
    system.api._access_token
    # >>> 7s9yasdh9aeu21211add

    # Return the current refresh token:
    system.api.refresh_token
    # >>> 896sad86gudas87d6asd

    # Return the SimpliSafe™ user ID associated with this account:
    system.api.user_id
    # >>> 1234567

Refreshing Access Tokens
************************

It may be desirable to re-authenticate against the SimpliSafe™ API at some
point in the future (and without using a user's email and password). In that
case, it is recommended that you save the ``refresh_token`` property somewhere;
when it comes time to re-authenticate, simply:

.. code:: python

    simplisafe = await API.login_via_token(
        "<REFRESH TOKEN>", websession
    )

During usage, ``simplipy`` will automatically refresh the access token as needed.
At any point, the "dirtiness" of the token can be checked:

.. code:: python

    simplisafe = await API.login_via_token(
        "<REFRESH TOKEN>", websession
    )

    systems = await simplisafe.get_systems()
    for system in systems.items():
        # Assuming the access token was automatically refreshed:
        primary_system.api.refresh_token_dirty
        # >>> True

        # Once the dirtiness is confirmed, the dirty bit resets:
        primary_system.api.refresh_token_dirty
        # >>> False

Errors/Exceptions
*****************

``simplipy`` exposes several useful error types:

* ``simplipy.errors.SimplipyError``: a base error that all other ``simplipy``
  errors inherit from
* ``simplipy.errors.InvalidCredentialsError``: an error related to an invalid
  username/password combo
* ``simplipy.errors.PinError``: an error related to an invalid PIN operation,
  such as attempting to delete a reserved PIN (e.g., "master"), adding too many
  PINs, etc.
* ``simplipy.errors.RequestError``: an error related to HTTP requests that return
  something other than a ``200`` response code
