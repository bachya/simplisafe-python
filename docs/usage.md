# Usage

## Installation

```bash
pip install simplisafe-python
```

## Python Versions

`simplisafe-python` is currently supported on:

- Python 3.8
- Python 3.9
- Python 3.10

## SimpliSafe™ Plans

SimpliSafe™ offers several [monitoring plans](https://support.simplisafe.com/hc/en-us/articles/360023809972-What-are-the-service-plan-options-).
Only the **Standard** and **Interactive** plans work with this library.

Please note that only Interactive plans can access sensor values and set the system
state; using the API with a Standard plan will be limited to retrieving the current
system state.

## Accessing the API

First, authenticate using your SimpliSafe™ username/email and password:

```python
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
```

This process creates an object in a "pending" state, which now awaits two-factor
authentication. You can find the type of two-factor authentication by looking at the
`auth_state` property:

```python
# If your account uses email-based two-factor authentication:
api.auth_state
# >>> simplipy.api.AuthStates.PENDING_2FA_EMAIL

# If your account uses SMS-based two-factor authentication:
api.auth_state
# >>> simplipy.api.AuthStates.PENDING_2FA_SMS
```

### Performing Email-Based Two-Factor Authentication

This type of two-factor authentication requires you to click a link in an email from
SimpliSafe™. At any point, you can see if two-factor authentication is complete:

```python
api.async_verify_2fa_email()
```

If the two-factor authentication hasn't succeeded yet, `simplipy` will raise a
{meth}`Verify2FAPending  <simplipy.errors.Verify2FAPending>` exception. If it has
succeeded, the {meth}`API  <simplipy.api.API>` object is ready to use.

A typical pattern in this scenario would be to loop and regularly test for
authentication (eventually timing out as appropriate):

```python
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
```

### Performing SMS-Based Two-Factor Authentication

This type of two-factor authentication requires you to input a code received via SMS.
After you receive the code, you verify it like this:

```python
api.async_verify_2fa_sms("<CODE>")
```

If the two-factor authentication hasn't succeeded yet, `simplipy` will raise a
{meth}`InvalidCredentialsError  <simplipy.errors.InvalidCredentialsError>` exception.
If it has succeeded, the {meth}`API  <simplipy.api.API>` object is ready to use.

```python
try:
   await api.async_verify_2fa_sms("<CODE>")
except InvalidCredentialsError as err:
   print("Invalid SMS 2FA code")

# Ready to use!
```

### Key API Object Properties

The {meth}`API <simplipy.api.API>` object contains several sensitive properties to be
aware of:

```python
# Return the current access token:
api.access_token
# >>> 7s9yasdh9aeu21211add

# Return the current refresh token:
api.refresh_token
# >>> 896sad86gudas87d6asd

# Return the SimpliSafe™ user ID associated with this account:
api.user_id
# >>> 1234567
```

Remember three essential characteristics of refresh tokens:

1. Refresh tokens can only be used once.
2. SimpliSafe™ will invalidate active tokens if you change your password.
3. Given the unofficial nature of the SimpliSafe™ API, we do not know how long refresh
   tokens are valid – we assume they'll last indefinitely, but that information may
   change.

### Creating a New API Object with the Refresh Token

It is cumbersome to call
{meth}`API.async_from_credentials <simplipy.api.API.async_from_credentials>` every time
you want a new {meth}`API <simplipy.api.API>` object. Therefore, *after* initial
authentication, call
{meth}`API.async_from_refresh_token <simplipy.api.API.async_from_refresh_token>`,
passing the {meth}`refresh_token <simplipy.api.API.refresh_token>` from the previous
{meth}`API <simplipy.api.API>` object. A common practice is to save a valid refresh
token to a filesystem/database/etc. and retrieve it later.

```python
import asyncio

from aiohttp import ClientSession
import simplipy


async def async_get_refresh_token() -> str:
    """Get a refresh token from storage."""
    # ...


async def main() -> None:
    """Create the aiohttp session and run."""
    async with ClientSession() as session:
        refresh_token = await async_get_refresh_token()
        api = await simplipy.API.async_from_refresh_token(
            refresh_token, session=session
        )

        # ...


asyncio.run(main())
```

After a new {meth}`API <simplipy.api.API>` object is created via
{meth}`API.async_from_refresh_token <simplipy.api.API.async_from_refresh_token>`, it
comes with its own, new refresh token; this can be used to follow the same
re-authentication process into perpetuity.

### Refreshing an Access Token During Runtime

In general, you do not need to worry about refreshing the access token within an
{meth}`API <simplipy.api.API>` object's normal operations; if an
{meth}`API <simplipy.api.API>` object encounters an error that indicates an expired access token, it will automatically attempt to use the refresh token it has.

However, should you need to refresh an access token manually at runtime, you can use the
{meth}`async_refresh_access_token <simplipy.api.API.async_refresh_access_token>` method.

### A VERY IMPORTANT NOTE ABOUT TOKENS

**It is vitally important not to let these tokens leave your control.** If
exposed, savvy attackers could use them to view and alter your system's state. **You
have been warned; proper storage/usage of tokens is solely your responsibility.**
