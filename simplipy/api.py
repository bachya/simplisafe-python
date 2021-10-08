"""Define functionality for interacting with the SimpliSafe API."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
import sys
from typing import TYPE_CHECKING, Any, Callable

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError
import backoff

from simplipy.const import DEFAULT_USER_AGENT, LOGGER
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
from simplipy.websocket import WebsocketClient

API_URL_HOSTNAME = "api.simplisafe.com"
API_URL_BASE = f"https://{API_URL_HOSTNAME}/v1"

DEFAULT_EXPIRATION_PADDING = 300
DEFAULT_REQUEST_RETRIES = 4
DEFAULT_TIMEOUT = 10


def get_expiration_datetime(expires_in_seconds: int) -> datetime:
    """Get a token expiration datetime as an offset of UTC now + a number of seconds.

    Note that we pad the value to ensure the token doesn't expire without us knowing.
    """
    return datetime.utcnow() + (
        timedelta(seconds=expires_in_seconds - DEFAULT_EXPIRATION_PADDING)
    )


class API:  # pylint: disable=too-many-instance-attributes
    """An API object to interact with the SimpliSafe cloud.

    Note that this class shouldn't be instantiated directly; instead, the
    :meth:`simplipy.api.API.async_from_auth` and :meth:`simplipy.api.API.async_from_refresh_token`
    methods should be used.

    :param session: The ``aiohttp`` ``ClientSession`` session used for all HTTP requests
    :type session: ``aiohttp.client.ClientSession``
    :param request_retries: The default number of request retries to use
    :type request_retries: ``int``
    """

    def __init__(
        self,
        *,
        session: ClientSession,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
    ) -> None:
        """Initialize."""
        self._refresh_token_listeners: list[Callable[..., None]] = []
        self.session: ClientSession = session

        # These will get filled in after initial authentication:
        self._access_token_expire_dt: datetime | None = None
        self._backoff_refresh_lock = asyncio.Lock()
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.subscription_data: dict[int, Any] = {}
        self.user_id: int | None = None
        self.websocket: WebsocketClient | None = None

        # Implement a version of the request coroutine, but with backoff/retry logic:
        self.request = backoff.on_exception(
            backoff.expo,
            ClientResponseError,
            jitter=backoff.random_jitter,
            logger=LOGGER,
            max_tries=request_retries,
            on_backoff=self._async_handle_on_backoff,
            on_giveup=self._async_handle_on_giveup,
        )(self._async_request)

    @classmethod
    async def async_from_auth(
        cls,
        authorization_code: str,
        code_verifier: str,
        *,
        session: ClientSession,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
    ) -> API:
        """Get an authenticated API object from an Authorization Code and Code Verifier.

        :param authorization_code: The Authorization Code
        :type authorization_code: ``str``
        :param code_verifier: The Code Verifier
        :type code_verifier: ``str``
        :param session: The ``aiohttp`` ``ClientSession`` session used for all HTTP requests
        :type session: ``aiohttp.client.ClientSession``
        :param request_retries: The default number of request retries to use
        :type request_retries: ``int``
        :rtype: :meth:`simplipy.api.API`
        """
        api = cls(session=session, request_retries=request_retries)

        try:
            token_resp = await api._async_request(
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

        api._access_token_expire_dt = get_expiration_datetime(token_resp["expires_in"])
        api.access_token = token_resp["access_token"]
        api.refresh_token = token_resp["refresh_token"]
        await api._async_post_init()
        return api

    @classmethod
    async def async_from_refresh_token(
        cls,
        refresh_token: str,
        session: ClientSession,
        *,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
    ) -> API:
        """Get an authenticated API object from a refresh token.

        :param refresh_token: The refresh token
        :type refresh_token: ``str``
        :param session: The ``aiohttp`` ``ClientSession`` session used for all HTTP requests
        :type session: ``aiohttp.client.ClientSession``
        :param request_retries: The default number of request retries to use
        :type request_retries: ``int``
        :rtype: :meth:`simplipy.api.API`
        """
        api = cls(session=session, request_retries=request_retries)
        api.refresh_token = refresh_token
        await api._async_refresh_access_token()
        await api._async_post_init()
        return api

    async def _async_handle_on_backoff(self, _: dict[str, Any]) -> None:
        """Handle a backoff retry."""
        err_info = sys.exc_info()
        err: ClientResponseError = err_info[1].with_traceback(err_info[2])  # type: ignore

        if err.status == 401 or err.status == 403:
            if TYPE_CHECKING:
                assert self._access_token_expire_dt

            # Since we might have multiple requests (each running their own retry
            # sequence) land here, we only refresh the access token if it hasn't
            # been refreshed within the expiration window (and we lock the attempt so
            # other requests can't try it at the same time):
            async with self._backoff_refresh_lock:
                if datetime.utcnow() < self._access_token_expire_dt:
                    return

                LOGGER.info("401 detected; attempting refresh token")
                await self._async_refresh_access_token()

    async def _async_handle_on_giveup(self, _: dict[str, Any]) -> None:
        """Handle a give up after retries are exhausted."""
        err_info = sys.exc_info()
        err = err_info[1].with_traceback(err_info[2])  # type: ignore
        raise RequestError(err) from err

    async def _async_post_init(self) -> None:
        """Perform some post-init actions."""
        auth_check_resp = await self._async_request("get", "api/authCheck")
        self.user_id = auth_check_resp["userId"]
        self.websocket = WebsocketClient(self)

    async def _async_refresh_access_token(self) -> None:
        """Update access/refresh tokens from a refresh token."""
        try:
            token_resp = await self._async_request(
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

        self._access_token_expire_dt = get_expiration_datetime(token_resp["expires_in"])
        self.access_token = token_resp["access_token"]
        self.refresh_token = token_resp["refresh_token"]

        for callback in self._refresh_token_listeners:
            callback(self.refresh_token)

    async def _async_request(
        self, method: str, endpoint: str, url_base: str = API_URL_BASE, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute an API request."""
        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault("Host", API_URL_HOSTNAME)
        kwargs["headers"]["Content-Type"] = "application/json; charset=utf-8"
        kwargs["headers"]["User-Agent"] = DEFAULT_USER_AGENT
        if self.access_token:
            kwargs["headers"]["Authorization"] = f"Bearer {self.access_token}"

        data: dict[str, Any] | str = {}
        async with self.session.request(
            method, f"{url_base}/{endpoint}", **kwargs
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

            LOGGER.debug("Data received from /%s: %s", endpoint, data)

            if data and data.get("type") == "NoRemoteManagement":
                raise EndpointUnavailableError(
                    f"Endpoint unavailable in plan: {endpoint}"
                ) from None

            resp.raise_for_status()

        return data

    def add_refresh_token_listener(
        self, callback: Callable[..., None]
    ) -> Callable[..., None]:
        """Add a listener that should be triggered when tokens are refreshed.

        Note that callbacks should expect to receive a refresh token as a parameter.

        :param callback: The method to call after receiving an event.
        :type callback: ``Callable[..., None]``
        """
        self._refresh_token_listeners.append(callback)

        def remove() -> None:
            """Remove the callback."""
            self._refresh_token_listeners.remove(callback)

        return remove

    async def async_get_systems(self) -> dict[int, SystemV2 | SystemV3]:
        """Get systems associated to the associated SimpliSafe account.

        In the dict that is returned, the keys are the subscription ID and the values
        are actual ``System`` objects.

        :rtype: ``Dict[int, simplipy.system.System]``
        """
        systems: dict[int, SystemV2 | SystemV3] = {}

        await self.async_update_subscription_data()

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
            await system.async_update(include_subscription=False)
            system.generate_device_objects()
            systems[sid] = system

        return systems

    async def async_update_subscription_data(self) -> None:
        """Get the latest subscription data."""
        subscription_resp = await self.request(
            "get", f"users/{self.user_id}/subscriptions", params={"activeOnly": "true"}
        )
        self.subscription_data = {
            subscription["sid"]: subscription
            for subscription in subscription_resp["subscriptions"]
        }
