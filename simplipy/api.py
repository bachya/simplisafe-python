"""Define a SimpliSafe account."""
import asyncio
import base64
from json.decoder import JSONDecodeError
from typing import Dict, Optional, Union
from uuid import uuid4

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from simplipy.const import LOGGER
from simplipy.errors import (
    EndpointUnavailable,
    InvalidCredentialsError,
    PendingAuthorizationError,
    RequestError,
)
from simplipy.system.v2 import SystemV2
from simplipy.system.v3 import SystemV3

API_URL_HOSTNAME = "api.simplisafe.com"
API_URL_BASE = f"https://{API_URL_HOSTNAME}/v1"
API_URL_MFA_OOB = "http://simplisafe.com/oauth/grant-type/mfa-oob"

DEFAULT_APP_VERSION = "1.62.0"
DEFAULT_REQUEST_RETRIES = 3
DEFAULT_REQUEST_RETRY_INTERVAL = 3
DEFAULT_TIMEOUT = 10
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/13.1.2 Safari/605.1.15"
)

CLIENT_ID_TEMPLATE = "{0}.WebApp.simplisafe.com"
DEVICE_ID_TEMPLATE = (
    'WebApp; useragent="Safari 13.1 (SS-ID: {0}) / macOS 10.15.6"; uuid="{1}"; id="{0}"'
)


def generate_device_id(client_id: str) -> str:
    """Generate a random 10-character ID to use as the SimpliSafe device ID."""
    seed = base64.b64encode(client_id.encode()).decode()[:10]
    return f"{seed[:5]}-{seed[5:]}"


class API:  # pylint: disable=too-many-instance-attributes
    """An API object to interact with the SimpliSafe cloud.

    Note that this class shouldn't be instantiated directly; instead, the
    :meth:`simplipy.api.login` method should be used.

    :param email: A SimpliSafe email address
    :type email: ``str``
    :param password: A SimpliSafe password
    :type password: ``str``
    :param session: The ``aiohttp`` ``ClientSession`` session used for all HTTP requests
    :type session: ``aiohttp.client.ClientSession``
    :param client_id: The SimpliSafe client ID to use for this API object
    :type client_id: ``str``
    :param request_retries: The default number of request retries to use
    :type request_retries: ``str``
    :param request_retry_interval: The default retry delay
    :type request_retry_interval: ``str``
    """

    def __init__(
        self,
        email: str,
        password: str,
        *,
        session: Optional[ClientSession] = None,
        client_id: Optional[str] = None,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
        request_retry_interval: int = DEFAULT_REQUEST_RETRY_INTERVAL,
    ) -> None:
        """Initialize."""
        self._client_id = client_id or str(uuid4())
        self._client_id_string = CLIENT_ID_TEMPLATE.format(self._client_id)
        self._device_id_string = DEVICE_ID_TEMPLATE.format(
            generate_device_id(self._client_id), self._client_id
        )
        self._email = email
        self._password = password
        self._reauth_tried = False
        self._refresh_tried = False
        self._request_retries = request_retries
        self._request_retry_interval = request_retry_interval
        self._session: ClientSession = session

        # These will get filled in after initial authentication:
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self.subscription_data: Dict[int, dict] = {}
        self.user_id: Optional[int] = None

    async def _authenticate(self, payload: dict) -> None:
        """Authenticate the API object using an authentication payload."""
        LOGGER.debug("Authentication payload: %s", payload)

        token_resp = await self._single_request("post", "api/token", json=payload)

        if "mfa_token" in token_resp:
            mfa_challenge_response = await self._single_request(
                "post",
                "api/mfa/challenge",
                json={
                    "challenge_type": "oob",
                    "client_id": self._client_id_string,
                    "mfa_token": token_resp["mfa_token"],
                },
            )

            await self._single_request(
                "post",
                "api/token",
                json={
                    "client_id": self._client_id_string,
                    "grant_type": API_URL_MFA_OOB,
                    "mfa_token": token_resp["mfa_token"],
                    "oob_code": mfa_challenge_response["oob_code"],
                    "scope": "offline_access",
                },
            )

            raise PendingAuthorizationError(
                f"Check your email for an MFA link, then use {self._client_id} "
                "as the client_id parameter in future API calls"
            )

        # Set access and refresh tokens:
        self._access_token = token_resp["access_token"]
        self._refresh_token = token_resp["refresh_token"]

        # Fetch the SimpliSafe user ID:
        auth_check_resp = await self._single_request("get", "api/authCheck")
        self.user_id = auth_check_resp["userId"]

    async def _refresh_access_token(self, refresh_token: Optional[str]) -> None:
        """Regenerate an access token.

        :param refresh_token: The refresh token to use
        :type refresh_token: str
        """
        await self._authenticate(
            {
                "grant_type": "refresh_token",
                "client_id": self._client_id,
                "refresh_token": refresh_token,
            }
        )

    async def _single_request(  # pylint: disable=too-many-statements,too-many-branches
        self, method: str, endpoint: str, **kwargs
    ) -> dict:
        """Make a single API request."""
        kwargs.setdefault("headers", {})
        if self._access_token:
            kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"
        kwargs["headers"]["Content-Type"] = "application/json; charset=utf-8"
        kwargs["headers"]["Host"] = API_URL_HOSTNAME
        kwargs["headers"]["User-Agent"] = DEFAULT_USER_AGENT

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        data = {}
        try:
            async with session.request(
                method, f"{API_URL_BASE}/{endpoint}", **kwargs
            ) as resp:
                try:
                    data = await resp.json(content_type=None)
                except JSONDecodeError:
                    message = await resp.text()
                    data = {"error": message}

                if isinstance(data, str):
                    # In some cases, the SimpliSafe API will return a quoted string
                    # in its response body (e.g., "\"Unauthorized\""), which is
                    # technically valid JSON. Additionally, SimpliSafe sets that
                    # response's Content-Type header to application/json (#smh).
                    # Together, these factors will allow a non-true-JSON  payload to
                    # escape the try/except above. So, if we get here, we use the
                    # string value (with quotes removed) to raise an error:
                    message = data.replace('"', "")
                    data = {"error": message}

                resp.raise_for_status()
        except ClientError as err:
            # If we get an "error" related to MFA, the response body data is
            # necessary for continuing on, so we swallow the error and return
            # that data:
            if data.get("error") == "mfa_required":
                return data

            if data.get("type") == "NoRemoteManagement":
                raise EndpointUnavailable(
                    f"Endpoint unavailable in plan: {endpoint}"
                ) from None

            if "401" in str(err):
                if not self._access_token:
                    raise InvalidCredentialsError("Invalid credentials") from err

                if not self._refresh_tried:
                    LOGGER.info("401 detected; attempting refresh token")
                    self._refresh_tried = True
                    await self._refresh_access_token(self._refresh_token)
                    return await self._single_request(method, endpoint, **kwargs)

                if not self._reauth_tried:
                    LOGGER.info("Another 401 detected; attempting full reauth")
                    self._reauth_tried = True
                    await self.login()
                    return await self._single_request(method, endpoint, **kwargs)

                raise InvalidCredentialsError("Invalid credentials") from err

            if "403" in str(err):
                raise InvalidCredentialsError("Unauthorized") from None

            raise err
        finally:
            if not use_running_session:
                await session.close()

        LOGGER.debug("Data received from /%s: %s", endpoint, data)

        self._refresh_tried = False
        self._reauth_tried = False

        return data

    async def login(self) -> None:
        """Authenticate the API object (making it ready for requests)."""
        await self._authenticate(
            {
                "grant_type": "password",
                "username": self._email,
                "password": self._password,
                "client_id": self._client_id_string,
                "device_id": self._device_id_string,
                "app_version": DEFAULT_APP_VERSION,
                "scope": "offline_access",
            }
        )

    async def get_systems(self) -> Dict[int, Union[SystemV2, SystemV3]]:
        """Get systems associated to the associated SimpliSafe account.

        In the dict that is returned, the keys are the system ID and the values are
        actual ``System`` objects.

        :rtype: ``Dict[int, simplipy.system.System]``
        """
        await self.update_subscription_data()

        systems = {}

        for system_id, subscription in self.subscription_data.items():
            version = subscription["location"]["system"]["version"]

            system: Union[SystemV2, SystemV3]
            if version == 2:
                system = SystemV2(self, system_id)
            else:
                system = SystemV3(self, system_id)

            # Skip deactivated systems:
            if not system.active:
                LOGGER.info("Skipping deactivated system: %s", system_id)
                continue

            # Update the system, but don't include system data itself, since it will
            # already have been fetched when the API was first queried:
            await system.update(include_system=False)
            await system.generate_entities()
            systems[system_id] = system

        return systems

    async def request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request (with retry logic).

        :param method: The HTTP method to use
        :type method: ``str``
        :param endpoint: The relative SimpliSafe API endpoint to hit
        :type endpoint: ``str``
        :rtype: ``dict``
        """
        retries = 0
        while retries < self._request_retries:
            try:
                data = await self._single_request(method, endpoint, **kwargs)
                break
            except ClientError as err:
                LOGGER.warning(
                    "Error while requesting /%s: %s (attempt %s of %s)",
                    endpoint,
                    err,
                    retries + 1,
                    self._request_retries,
                )
                retries += 1
                await asyncio.sleep(self._request_retry_interval)
        else:
            raise RequestError(
                f"Requesting /{endpoint} failed after {retries} tries"
            ) from None

        return data

    async def update_subscription_data(self) -> None:
        """Update our internal "raw data" listing of subscriptions."""
        subscription_resp = await self.request(
            "get", f"users/{self.user_id}/subscriptions", params={"activeOnly": "true"}
        )

        for subscription in subscription_resp["subscriptions"]:
            if "version" not in subscription["location"]["system"]:
                LOGGER.error(
                    "Skipping location with missing system data: %s",
                    subscription["location"]["sid"],
                )
                continue

            self.subscription_data[subscription["sid"]] = subscription


async def get_api(
    email: str,
    password: str,
    *,
    session: Optional[ClientSession] = None,
    client_id: Optional[str] = None,
    request_retries: int = DEFAULT_REQUEST_RETRIES,
    request_retry_interval: int = DEFAULT_REQUEST_RETRY_INTERVAL,
) -> API:
    """Return an authenticated API object.

    :param email: A SimpliSafe email address
    :type email: ``str``
    :param password: A SimpliSafe password
    :type password: ``str``
    :param session: An ``aiohttp`` ``ClientSession``
    :type session: ``aiohttp.client.ClientSession``
    :param client_id: The SimpliSafe client ID to use for this API object
    :type client_id: ``str``
    :param request_retries: The default number of request retries to use
    :type request_retries: ``str``
    :param request_retry_interval: The default retry delay
    :type request_retry_interval: ``str``
    :rtype: :meth:`simplipy.API`
    """
    api = API(
        email,
        password,
        session=session,
        client_id=client_id,
        request_retries=request_retries,
        request_retry_interval=request_retry_interval,
    )
    await api.login()
    return api
