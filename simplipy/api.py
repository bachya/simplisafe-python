"""Define functionality for interacting with the SimpliSafe API."""
from __future__ import annotations

from json.decoder import JSONDecodeError
import sys
from typing import Any

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientResponseError
import backoff

from simplipy.const import LOGGER
from simplipy.errors import (
    EndpointUnavailableError,
    InvalidCredentialsError,
    RequestError,
)
from simplipy.system.v2 import SystemV2
from simplipy.system.v3 import SystemV3
from simplipy.util.auth import (
    AUTH_URL_BASE,
    AUTH_URL_HOSTNAME,
    DEFAULT_CLIENT_ID,
    DEFAULT_REDIRECT_URI,
)

API_URL_HOSTNAME = "api.simplisafe.com"
API_URL_BASE = f"https://{API_URL_HOSTNAME}/v1"

DEFAULT_REQUEST_RETRIES = 4
DEFAULT_TIMEOUT = 10
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15"
)


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
    :type request_retries: ``int``
    """

    def __init__(
        self,
        *,
        session: ClientSession | None = None,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
    ) -> None:
        """Initialize."""
        self._session: ClientSession | None = session

        # These will get filled in after initial authentication:
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.subscription_data: dict[int, Any] = {}
        self.user_id: int | None = None

        # Implement a version of the request coroutine, but with backoff/retry logic:
        self.request = backoff.on_exception(
            backoff.expo,
            ClientResponseError,
            logger=LOGGER,
            max_tries=request_retries,
            on_backoff=self._handle_on_backoff,
            on_giveup=self._handle_on_giveup,
        )(self._request)

    @classmethod
    async def from_auth(
        cls,
        authorization_code: str,
        code_verifier: str,
        *,
        session: ClientSession | None = None,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
    ) -> API:
        """Get an authenticated API object from an Auth0 code/verifier."""
        api = cls(session=session, request_retries=request_retries)

        try:
            token_resp = await api._request(
                "post",
                "oauth/token",
                url_base=AUTH_URL_BASE,
                headers={"Host": AUTH_URL_HOSTNAME},
                json={
                    "grant_type": "authorization_code",
                    "client_id": DEFAULT_CLIENT_ID,
                    "code_verifier": code_verifier,
                    "code": authorization_code,
                    "redirect_uri": DEFAULT_REDIRECT_URI,
                },
            )
        except ClientResponseError as err:
            if err.status == 401 or err.status == 403:
                raise InvalidCredentialsError("Invalid credentials") from err
            raise RequestError(err) from err

        api.access_token = token_resp["access_token"]
        api.refresh_token = token_resp["refresh_token"]
        await api._update_user_id()
        return api

    @classmethod
    async def from_refresh_token(
        cls,
        refresh_token: str,
        *,
        session: ClientSession | None = None,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
    ) -> API:
        """Get an authenticated API object from a refresh token."""
        api = cls(session=session, request_retries=request_retries)
        api.refresh_token = refresh_token
        await api._refresh_access_token()
        await api._update_user_id()
        return api

    async def _handle_on_backoff(self, _: dict[str, Any]) -> None:
        """Handle a backoff retry."""
        err_info = sys.exc_info()
        err = err_info[1].with_traceback(err_info[2])  # type: ignore

        if err.status == 401 or err.status == 403:
            LOGGER.info("401 detected; attempting refresh token")
            await self._refresh_access_token()

    async def _handle_on_giveup(self, _: dict[str, Any]) -> None:
        """Handle a give up after retries are exhausted."""
        err_info = sys.exc_info()
        err = err_info[1].with_traceback(err_info[2])  # type: ignore
        raise RequestError(err) from err

    async def _refresh_access_token(self) -> None:
        """Update access/refresh tokens from a refresh token."""
        try:
            token_resp = await self._request(
                "post",
                "oauth/token",
                url_base=AUTH_URL_BASE,
                headers={"Host": AUTH_URL_HOSTNAME},
                json={
                    "grant_type": "refresh_token",
                    "client_id": DEFAULT_CLIENT_ID,
                    "refresh_token": self.refresh_token,
                },
            )
        except ClientResponseError as err:
            if err.status == 401 or err.status == 403:
                raise InvalidCredentialsError("Invalid refresh token") from err
            raise RequestError(err) from err

        self.access_token = token_resp["access_token"]
        self.refresh_token = token_resp["refresh_token"]

    async def _request(
        self, method: str, endpoint: str, url_base: str = API_URL_BASE, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute an API request.

        :param method: The HTTP method to use
        :type method: ``str``
        :param endpoint: The relative SimpliSafe API endpoint to hit
        :type endpoint: ``str``
        :param url_base: The base URL to use
        :type url_base: ``str``
        :rtype: ``dict``
        """
        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault("Host", API_URL_HOSTNAME)
        kwargs["headers"]["Content-Type"] = "application/json; charset=utf-8"
        kwargs["headers"]["User-Agent"] = DEFAULT_USER_AGENT
        if self.access_token:
            kwargs["headers"]["Authorization"] = f"Bearer {self.access_token}"

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        assert session

        data: dict[str, Any] | str = {}
        async with session.request(method, f"{url_base}/{endpoint}", **kwargs) as resp:
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

            LOGGER.debug("Data received from /%s: %s", endpoint, data)

            if data and data.get("type") == "NoRemoteManagement":
                raise EndpointUnavailableError(
                    f"Endpoint unavailable in plan: {endpoint}"
                ) from None

            resp.raise_for_status()

        if not use_running_session:
            await session.close()

        return data

    async def _update_user_id(self) -> None:
        """Verify and update the user ID."""
        auth_check_resp = await self._request("get", "api/authCheck")
        self.user_id = auth_check_resp["userId"]

    async def get_systems(self) -> dict[int, SystemV2 | SystemV3]:
        """Get systems associated to the associated SimpliSafe account.

        In the dict that is returned, the keys are the subscription ID and the values
        are actual ``System`` objects.

        :rtype: ``Dict[int, simplipy.system.System]``
        """
        systems: dict[int, SystemV2 | SystemV3] = {}

        await self.update_subscription_data()

        for sid, subscription in self.subscription_data.items():
            if not subscription["activated"] != 0:
                LOGGER.info("Skipping inactive subscription: %s", sid)
                continue

            # if "system" not in subscription["location"]:
            if not subscription["location"].get("system"):
                LOGGER.error("Skipping subscription with missing system data: %s", sid)
                continue

            system: SystemV2 | SystemV3
            version = subscription["location"]["system"]["version"]
            if version == 2:
                system = SystemV2(self, sid)
            else:
                system = SystemV3(self, sid)

            # Update the system, but don't include subscription data itself, since it
            # will already have been fetched when the API was first queried:
            await system.update(include_subscription=False)
            system.generate_device_objects()
            systems[sid] = system

        return systems

    async def update_subscription_data(self) -> None:
        """Get the latest subscription data."""
        subscription_resp = await self.request(
            "get", f"users/{self.user_id}/subscriptions", params={"activeOnly": "true"}
        )
        self.subscription_data = {
            subscription["sid"]: subscription
            for subscription in subscription_resp["subscriptions"]
        }
