"""Define a SimpliSafe account."""
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, Type, TypeVar
from uuid import UUID, uuid4

from aiohttp import BasicAuth, ClientSession
from aiohttp.client_exceptions import ClientError

from simplipy.errors import InvalidCredentialsError, RequestError
from simplipy.system import System
from simplipy.system.v2 import SystemV2
from simplipy.system.v3 import SystemV3
from simplipy.websocket import Websocket

_LOGGER: logging.Logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT: str = "SimpliSafe/2105 CFNetwork/902.2 Darwin/17.7.0"
DEFAULT_AUTH_USERNAME: str = "{0}.2074.0.0.com.simplisafe.mobile"

SYSTEM_MAP: Dict[int, Type[System]] = {2: SystemV2, 3: SystemV3}

API_URL_HOSTNAME: str = "api.simplisafe.com"
API_URL_BASE: str = f"https://{API_URL_HOSTNAME}/v1"

ApiType = TypeVar("ApiType", bound="API")


class API:  # pylint: disable=too-many-instance-attributes
    """An API object to interact with the SimpliSafe cloud.

    Note that this class shouldn't be instantiated directly; instead, the
    :meth:`simplipy.API.login_via_credentials` and :meth:`simplipy.API.login_via_token`
    class methods should be used.

    :param websession: The ``aiohttp`` ``ClientSession`` session used for all HTTP requests
    :type websession: ``aiohttp.client.ClientSession``
    """

    def __init__(self, websession: ClientSession) -> None:
        """Initialize."""
        self._access_token: str = ""
        self._access_token_expire: Optional[datetime] = None
        self._actively_refreshing: bool = False
        self._refresh_token: str = ""
        self._uuid: UUID = uuid4()
        self._websession: ClientSession = websession
        self.email: Optional[str] = None
        self.user_id: Optional[int] = None
        self.websocket: Websocket = Websocket()

    @property
    def access_token(self) -> str:
        """Return the current access token.

        :rtype: ``str``
        """
        return self._access_token

    @property
    def refresh_token(self) -> str:
        """Return the current refresh token.

        :rtype: ``str``
        """
        return self._refresh_token

    @classmethod
    async def login_via_credentials(
        cls: Type[ApiType], email: str, password: str, websession: ClientSession
    ) -> ApiType:
        """Create an API object from a email address and password.

        :param email: A SimpliSafe email address
        :type email: ``str``
        :param password: A SimpliSafe password
        :type password: ``str``
        :param websession: An ``aiohttp`` ``ClientSession``
        :type websession: ``aiohttp.client.ClientSession``
        :rtype: :meth:`simplipy.API`
        """
        klass = cls(websession)
        klass.email = email

        await klass._authenticate(  # pylint: disable=protected-access
            {"grant_type": "password", "username": email, "password": password}
        )

        return klass

    @classmethod
    async def login_via_token(
        cls: Type[ApiType], refresh_token: str, websession: ClientSession
    ) -> ApiType:
        """Create an API object from a refresh token.

        :param refresh_token: A SimpliSafe refresh token
        :type refresh_token: ``str``
        :param websession: An ``aiohttp`` ``ClientSession``
        :type websession: ``aiohttp.client.ClientSession``
        :rtype: :meth:`simplipy.API`
        """
        klass = cls(websession)
        await klass.refresh_access_token(refresh_token)
        return klass

    async def _authenticate(self, payload_data: dict) -> None:
        """Request a new token."""
        token_resp: dict = await self._request(
            "post",
            "api/token",
            data=payload_data,
            auth=BasicAuth(  # nosec
                login=DEFAULT_AUTH_USERNAME.format(self._uuid),
                password="",
                encoding="latin1",
            ),
        )

        self._access_token = token_resp["access_token"]
        self._access_token_expire = datetime.now() + timedelta(
            seconds=int(token_resp["expires_in"]) - 60
        )
        self._refresh_token = token_resp["refresh_token"]

        auth_check_resp: dict = await self._request("get", "api/authCheck")
        self.user_id = auth_check_resp["userId"]

        await self.websocket.async_init(self._access_token, self.user_id)

    async def _get_subscription_data(self) -> dict:
        """Get the latest location-level data."""
        subscription_resp: dict = await self._request(
            "get", f"users/{self.user_id}/subscriptions", params={"activeOnly": "true"}
        )

        _LOGGER.debug("Subscription response: %s", subscription_resp)

        return subscription_resp

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        **kwargs,
    ) -> dict:
        """Make a request."""
        if (
            self._access_token_expire
            and datetime.now() >= self._access_token_expire
            and not self._actively_refreshing
        ):
            self._actively_refreshing = True
            await self.refresh_access_token(self._refresh_token)

        if not headers:
            headers = {}
        if not kwargs.get("auth") and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        headers.update({"Host": API_URL_HOSTNAME, "User-Agent": DEFAULT_USER_AGENT})

        try:
            async with self._websession.request(
                method,
                f"{API_URL_BASE}/{endpoint}",
                headers=headers,
                params=params,
                data=data,
                json=json,
                **kwargs,
            ) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except ClientError as err:
            if "401" in str(err):
                if self._actively_refreshing:
                    raise InvalidCredentialsError(
                        "Repeated 401s despite refreshing access token"
                    )
                if self._refresh_token:
                    _LOGGER.info("401 detected; attempting refresh token")
                    self._access_token_expire = datetime.now()
                    return await self._request(
                        method,
                        endpoint,
                        headers=headers,
                        params=params,
                        data=data,
                        json=json,
                        **kwargs,
                    )
                raise InvalidCredentialsError("Invalid username/password")
            if "403" in str(err):
                if self.user_id:
                    _LOGGER.info("Endpoint unavailable in plan: %s", endpoint)
                    return {}
                raise InvalidCredentialsError(
                    f"User does not have permission to access {endpoint}"
                )

            raise RequestError(f"Error requesting data from {endpoint}: {err}")

    async def get_systems(self) -> Dict[str, System]:
        """Get systems associated to the associated SimpliSafe account.

        In the dict that is returned, the keys are the system ID and the values are
        actual ``System`` objects.

        :rtype: ``Dict[str, simplipy.system.System]``
        """
        subscription_resp: dict = await self._get_subscription_data()

        systems: Dict[str, System] = {}
        for system_data in subscription_resp["subscriptions"]:
            version = system_data["location"]["system"]["version"]
            system_class = SYSTEM_MAP[version]
            system = system_class(
                self._request, self._get_subscription_data, system_data["location"]
            )
            await system.update(include_system=False)
            systems[system_data["sid"]] = system

        return systems

    async def refresh_access_token(self, refresh_token: str) -> None:
        """Regenerate an access token.

        :param refresh_token: The refresh token to use
        :type refresh_token: str
        """
        await self._authenticate(
            {
                "grant_type": "refresh_token",
                "username": self.email,
                "refresh_token": refresh_token,
            }
        )

        self._actively_refreshing = False
