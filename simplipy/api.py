"""Define a SimpliSafe account."""
import base64
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
import logging
from typing import Dict, Optional, Type, TypeVar
from uuid import uuid4

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from simplipy.errors import (
    EndpointUnavailable,
    InvalidCredentialsError,
    PendingAuthorizationError,
    RequestError,
)
from simplipy.system import System
from simplipy.system.v2 import SystemV2
from simplipy.system.v3 import SystemV3
from simplipy.websocket import Websocket

_LOGGER: logging.Logger = logging.getLogger(__name__)

API_URL_HOSTNAME: str = "api.simplisafe.com"
API_URL_BASE: str = f"https://{API_URL_HOSTNAME}/v1"
API_URL_MFA_OOB: str = "http://simplisafe.com/oauth/grant-type/mfa-oob"

DEFAULT_TIMEOUT: int = 10
DEFAULT_USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/13.1.2 Safari/605.1.15"
)

CLIENT_ID_TEMPLATE = "{0}.WebApp.simplisafe.com"
DEVICE_ID_TEMPLATE = (
    'WebApp; useragent="Safari 13.1 (SS-ID: {0}) / macOS 10.15.6"; uuid="{1}"; id="{0}"'
)

SYSTEM_MAP: Dict[int, Type[System]] = {2: SystemV2, 3: SystemV3}


ApiType = TypeVar("ApiType", bound="API")


def generate_device_id(client_id: str) -> str:
    """Generate a random 10-character ID to use as the SimpliSafe device ID."""
    seed = base64.b64encode(client_id.encode()).decode()[:10]
    return f"{seed[:5]}-{seed[5:]}"


class API:  # pylint: disable=too-many-instance-attributes
    """An API object to interact with the SimpliSafe cloud.

    Note that this class shouldn't be instantiated directly; instead, the
    :meth:`simplipy.API.login_via_credentials` and :meth:`simplipy.API.login_via_token`
    class methods should be used.

    :param session: The ``aiohttp`` ``ClientSession`` session used for all HTTP requests
    :type session: ``aiohttp.client.ClientSession``
    :param client_id: The SimpliSafe client ID to use for this API object
    :type client_id: ``str``
    """

    def __init__(
        self, *, client_id: str, session: Optional[ClientSession] = None
    ) -> None:
        """Initialize."""
        self._access_token: Optional[str] = None
        self._access_token_expire: Optional[datetime] = None
        self._actively_refreshing: bool = False
        self._refresh_token: Optional[str] = None
        self._session: ClientSession = session

        self._client_id = client_id if client_id else str(uuid4())
        self._client_id_string: str = CLIENT_ID_TEMPLATE.format(self._client_id)
        self._device_id: str = generate_device_id(self._client_id)

        self.email: Optional[str] = None
        self.user_id: Optional[int] = None
        self.websocket: Websocket = Websocket()

    @property
    def access_token(self) -> Optional[str]:
        """Return the current access token.

        :rtype: ``str``
        """
        return self._access_token

    @property
    def client_id(self) -> str:
        """Return the client ID of the API."""
        return self._client_id

    @property
    def client_id_string(self) -> str:
        """Return the client ID of the API."""
        return self._client_id_string

    @property
    def device_id(self) -> str:
        """Return the generated device ID for this API instance."""
        return self._device_id

    @property
    def refresh_token(self) -> Optional[str]:
        """Return the current refresh token.

        :rtype: ``str``
        """
        return self._refresh_token

    @classmethod
    async def login_via_credentials(
        cls: Type[ApiType],
        email: str,
        password: str,
        *,
        client_id: str,
        session: Optional[ClientSession] = None,
    ) -> ApiType:
        """Create an API object from a email address and password.

        :param email: A SimpliSafe email address
        :type email: ``str``
        :param password: A SimpliSafe password
        :type password: ``str``
        :param session: An ``aiohttp`` ``ClientSession``
        :type session: ``aiohttp.client.ClientSession``
        :param client_id: The SimpliSafe client ID to use for this API object
        :type client_id: ``str``
        :rtype: :meth:`simplipy.API`
        """
        klass = cls(session=session, client_id=client_id)
        klass.email = email

        await klass.authenticate(
            {
                "grant_type": "password",
                "username": email,
                "password": password,
                "client_id": klass.client_id_string,
                "device_id": DEVICE_ID_TEMPLATE.format(
                    klass.device_id, klass.client_id
                ),
                "app_version": "1.62.0",
                "scope": "offline_access",
            }
        )

        return klass

    @classmethod
    async def login_via_token(
        cls: Type[ApiType],
        refresh_token: str,
        *,
        client_id: str,
        session: Optional[ClientSession] = None,
    ) -> ApiType:
        """Create an API object from a refresh token.

        :param refresh_token: A SimpliSafe refresh token
        :type refresh_token: ``str``
        :param session: An ``aiohttp`` ``ClientSession``
        :type session: ``aiohttp.client.ClientSession``
        :param client_id: The SimpliSafe client ID to use for this API object
        :type client_id: ``str``
        :rtype: :meth:`simplipy.API`
        """
        klass = cls(session=session, client_id=client_id)
        await klass.refresh_access_token(refresh_token)
        return klass

    async def _get_subscription_data(self) -> dict:
        """Get the latest location-level data."""
        subscription_resp: dict = await self.request(
            "get", f"users/{self.user_id}/subscriptions", params={"activeOnly": "true"}
        )

        _LOGGER.debug(
            "users/%s/subscriptions response: %s", self.user_id, subscription_resp
        )

        return subscription_resp

    async def authenticate(self, payload: dict) -> None:
        """Authenticate the API object using an authentication payload."""
        _LOGGER.debug("Authentication payload: %s", payload)

        token_resp: dict = await self.request("post", "api/token", json=payload)

        if "mfa_token" in token_resp:
            mfa_challenge_response: dict = await self.request(
                "post",
                "api/mfa/challenge",
                json={
                    "challenge_type": "oob",
                    "client_id": self._client_id_string,
                    "mfa_token": token_resp["mfa_token"],
                },
            )

            await self.request(
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

        self._access_token = token_resp["access_token"]
        self._access_token_expire = datetime.now() + timedelta(
            seconds=int(token_resp["expires_in"]) - 60
        )
        self._refresh_token = token_resp["refresh_token"]

        auth_check_resp: dict = await self.request("get", "api/authCheck")
        self.user_id = auth_check_resp["userId"]

        await self.websocket.async_init(self._access_token, self.user_id)

    async def get_systems(self) -> Dict[str, System]:
        """Get systems associated to the associated SimpliSafe account.

        In the dict that is returned, the keys are the system ID and the values are
        actual ``System`` objects.

        :rtype: ``Dict[str, simplipy.system.System]``
        """
        subscription_resp: dict = await self._get_subscription_data()

        systems: Dict[str, System] = {}
        for system_data in subscription_resp["subscriptions"]:
            if "version" not in system_data["location"]["system"]:
                _LOGGER.error(
                    "Skipping location with missing system data: %s",
                    system_data["location"]["sid"],
                )
                continue

            version = system_data["location"]["system"]["version"]
            system_class = SYSTEM_MAP[version]
            system = system_class(
                self.request, self._get_subscription_data, system_data["location"]
            )
            await system.update(include_system=False)
            systems[system_data["sid"]] = system

        return systems

    async def request(  # pylint: disable=too-many-branches
        self, method: str, endpoint: str, **kwargs
    ) -> dict:
        """Make an API request."""
        if (
            self._access_token_expire
            and datetime.now() >= self._access_token_expire
            and not self._actively_refreshing
        ):
            _LOGGER.debug(
                "Need to refresh access token (expiration: %s)",
                self._access_token_expire,
            )
            self._actively_refreshing = True
            await self.refresh_access_token(self._refresh_token)

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

        async with session.request(
            method, f"{API_URL_BASE}/{endpoint}", **kwargs
        ) as resp:
            try:
                data = await resp.json(content_type=None)
            except JSONDecodeError:
                message = await resp.text()
                data = {"error": message}

            _LOGGER.debug("Data received from /%s: %s", endpoint, data)

            try:
                resp.raise_for_status()
            except ClientError as err:
                if data.get("error") == "mfa_required":
                    return data

                if data.get("type") == "NoRemoteManagement":
                    raise EndpointUnavailable(
                        f"Endpoint unavailable in plan: {endpoint}"
                    ) from None

                if "401" in str(err):
                    if self._actively_refreshing:
                        raise InvalidCredentialsError(
                            "Repeated 401s despite refreshing access token"
                        ) from None
                    if self._refresh_token:
                        _LOGGER.info("401 detected; attempting refresh token")
                        self._access_token_expire = datetime.now()
                        return await self.request(method, endpoint, **kwargs)
                    raise InvalidCredentialsError("Invalid username/password") from None

                raise RequestError(
                    f"There was an error while requesting /{endpoint}: {err}"
                ) from None
            finally:
                if not use_running_session:
                    await session.close()

        return data

    async def refresh_access_token(self, refresh_token: Optional[str]) -> None:
        """Regenerate an access token.

        :param refresh_token: The refresh token to use
        :type refresh_token: str
        """
        await self.authenticate(
            {
                "grant_type": "refresh_token",
                "client_id": self._client_id,
                "refresh_token": refresh_token,
            }
        )

        self._actively_refreshing = False
