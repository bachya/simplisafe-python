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
    simplisafe._access_token
    # >>> 7s9yasdh9aeu21211add

    # Return the current refresh token:
    simplisafe.refresh_token
    # >>> 896sad86gudas87d6asd

    # Return the SimpliSafe™ user ID associated with this account:
    simplisafe.user_id
    # >>> 1234567
