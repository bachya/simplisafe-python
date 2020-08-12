Advanced Usage
--------------

The SimpliSafe Object
*********************

Although 99% of users will focus primarily on the :meth:`System <simplipy.system.System>`
object and its associated objects, the ``SimpliSafe`` object created at the very
beginning of each example is useful for managing ongoing access to the API.

**VERY IMPORTANT NOTE:** the ``SimpliSafe`` object contains references to
SimpliSafe™ access and refresh tokens. **It is vitally important that you do
not let these tokens leave your control.** If exposed, savvy attackers could
use them to view and alter your system's state. **You have been warned; proper
usage of these properties is solely your responsibility.**

.. code:: python

    # Return the current access token:
    simplisafe.access_token
    # >>> 7s9yasdh9aeu21211add

    # Return the current refresh token:
    simplisafe.refresh_token
    # >>> 896sad86gudas87d6asd

    # Return the SimpliSafe™ user ID associated with this account:
    simplisafe.user_id
    # >>> 1234567

.. _refreshing-access-tokens:

Refreshing Access Tokens
************************

It may be desirable to re-authenticate against the SimpliSafe™ API at some
point in the future (and without using a user's email and password). In that
case, it is recommended that you save the ``refresh_token`` property somewhere;
when it comes time to re-authenticate, simply:

.. code:: python

    simplisafe = await simplipy.API.login_via_token(
        "<REFRESH TOKEN>", client_id="<UNIQUE IDENTIFIER>", session=session
    )

During usage, ``simplipy`` will automatically refresh the access token as needed.
At any point, the "dirtiness" of the token can be checked:

.. code:: python

    simplisafe = await simplipy.API.login_via_token(
        "<REFRESH TOKEN>", client_id="<UNIQUE IDENTIFIER>", session=session
    )

    # Assuming the access token was automatically refreshed:
    simplisafe.refresh_token_dirty
    # >>> True

    # Once the dirtiness is confirmed, the dirty bit resets:
    simplisafe.refresh_token_dirty
    # >>> False
