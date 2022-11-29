"""Define functionality for interacting with the SimpliSafe API."""
from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable
from datetime import datetime
from json.decoder import JSONDecodeError
from typing import Any, cast

import backoff
from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientResponseError

from simplipy.const import DEFAULT_USER_AGENT, LOGGER
from simplipy.errors import (
    InvalidCredentialsError,
    RequestError,
    SimplipyError,
    raise_on_data_error,
)
from simplipy.system.v2 import SystemV2
from simplipy.system.v3 import SystemV3
from simplipy.util import execute_callback
from simplipy.util.auth import (
    AUTH_URL_BASE,
    AUTH_URL_HOSTNAME,
    DEFAULT_CLIENT_ID,
    DEFAULT_REDIRECT_URI,
)
from simplipy.websocket import WebsocketClient

API_URL_HOSTNAME = "api.simplisafe.com"
API_URL_BASE = f"https://{API_URL_HOSTNAME}/v1"

DEFAULT_REQUEST_RETRIES = 4
DEFAULT_TIMEOUT = 10
DEFAULT_TOKEN_EXPIRATION_WINDOW = 5


class API:  # pylint: disable=too-many-instance-attributes
    """An API object to interact with the SimpliSafe cloud.

    Note that this class shouldn't be instantiated directly; instead, the
    :meth:`simplipy.api.API.async_from_auth` and
    :meth:`simplipy.api.API.async_from_refresh_token` methods should be used.

    Args:
        session: session: An optional ``aiohttp`` ``ClientSession``.
        request_retries: The default number of request retries to use.
    """

    def __init__(
        self,
        *,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
        session: ClientSession,
    ) -> None:
        """Initialize.

        Args:
            session: An optional ``aiohttp`` ``ClientSession``.
            request_retries: The default number of request retries to use.
        """
        self._refresh_token_callbacks: list[
            Callable[[str], Awaitable[None] | None]
        ] = []
        self._request_retries = request_retries
        self.session: ClientSession = session

        # These will get filled in after initial authentication:
        self._backoff_refresh_lock = asyncio.Lock()
        self._token_last_refreshed: datetime | None = None
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.subscription_data: dict[int, Any] = {}
        self.user_id: int | None = None
        self.websocket: WebsocketClient | None = None

        self.async_request = self._wrap_request_method(self._request_retries)

    @classmethod
    async def async_from_auth(
        cls,
        authorization_code: str,
        code_verifier: str,
        *,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
        session: ClientSession,
    ) -> API:
        """Get an authenticated API object from an Authorization Code and Code Verifier.

        Args:
            authorization_code: The Authorization Code.
            code_verifier: The Code Verifier.
            request_retries: The default number of request retries to use.
            session: An optional ``aiohttp`` ``ClientSession``.

        Returns:
            An authenticated API object.

        Raises:
            InvalidCredentialsError: Raised on invalid username/password.
            RequestError: Raised on general HTTP error.
            SimplipyError: Raised on an unknown error.
        """
        api = cls(session=session, request_retries=request_retries)

        try:
            token_data = await api._async_api_request(
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
            if err.status in (401, 403):
                raise InvalidCredentialsError("Invalid credentials") from err
            raise RequestError(err) from err
        except Exception as err:  # pylint: disable=broad-except
            raise SimplipyError(err) from err

        api._save_token_data_from_response(token_data)
        await api._async_post_init()
        return api

    @classmethod
    async def async_from_refresh_token(
        cls,
        refresh_token: str,
        *,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
        session: ClientSession,
    ) -> API:
        """Get an authenticated API object from a refresh token.

        Args:
            refresh_token: A refresh token.
            request_retries: The default number of request retries to use.
            session: An optional ``aiohttp`` ``ClientSession``.

        Returns:
            An authenticated API object.
        """
        api = cls(session=session, request_retries=request_retries)
        api.refresh_token = refresh_token
        await api.async_refresh_access_token()
        await api._async_post_init()
        return api

    async def _async_handle_on_backoff(self, _: dict[str, Any]) -> None:
        """Handle a backoff retry."""
        err_info = sys.exc_info()
        err: ClientResponseError = err_info[1].with_traceback(  # type: ignore
            err_info[2]
        )

        LOGGER.debug("Error during request attempt: %s", err)

        if err.status == 401 and self._token_last_refreshed:
            # Calculate the window between now and the last time the token was
            # refreshed:
            window = (datetime.utcnow() - self._token_last_refreshed).total_seconds()

            # Since we might have multiple requests (each running their own retry
            # sequence) land here, we only refresh the access token if it hasn't
            # been refreshed within the window (and we lock the attempt so other
            # requests can't try it at the same time):
            async with self._backoff_refresh_lock:
                if window < DEFAULT_TOKEN_EXPIRATION_WINDOW:
                    LOGGER.debug("Skipping refresh attempt since window hasn't busted")
                    return

                LOGGER.info("401 detected; attempting refresh token")
                await self.async_refresh_access_token()

    async def _async_post_init(self) -> None:
        """Perform some post-init actions."""
        auth_check_resp = await self._async_api_request("get", "api/authCheck")
        self.user_id = auth_check_resp["userId"]
        self.websocket = WebsocketClient(self)

    async def _async_api_request(
        self, method: str, endpoint: str, url_base: str = API_URL_BASE, **kwargs: Any
    ) -> dict[str, Any]:
        """Make an API request.

        Args:
            method: An HTTP method.
            endpoint: A relative API endpoint.
            url_base: The base URL of the API.
            **kwargs: Additional kwargs to send with the request.

        Returns:
            An API response payload.
        """
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
                data = {"type": "DataParsingError", "message": message}

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

            raise_on_data_error(data)
            resp.raise_for_status()

        return data

    @staticmethod
    def _handle_on_giveup(_: dict[str, Any]) -> None:
        """Handle a give up after retries are exhausted.

        Raises:
            RequestError: Raised upon an underlying HTTP error.
        """
        err_info = sys.exc_info()
        err = err_info[1].with_traceback(err_info[2])  # type: ignore
        raise RequestError(err) from err

    def _save_token_data_from_response(self, token_data: dict[str, Any]) -> None:
        """Save token data from a token response.

        Args:
            token_data: An API response payload.
        """
        self._token_last_refreshed = datetime.utcnow()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]

    @staticmethod
    def is_fatal_error(err: ClientResponseError) -> bool:
        """Determine whether a ClientResponseError is fatal and shouldn't be retried.

        In general, we retry anything outside of HTTP 4xx codes (client errors) with a
        few exceptions:

        1. 401: We catch this, refresh the access token, and retry the original request.
        2. 409: SimpliSafe base stations regular synchronize themselves with the API,
                which is where this error can occur; we can't control when/how that
                happens (e.g., we might query the API in the middle of a base station
                update), so it should be viewed as retryable.

        Args:
            err: An ``aiohttp`` ``ClientResponseError``

        Returns:
            Whether the error is a fatal one.
        """
        if err.status in (401, 409):
            return False
        return 400 <= err.status < 500

    def _wrap_request_method(
        self, request_retries: int
    ) -> Callable[..., Awaitable[dict[str, Any]]]:
        """Wrap the request method in backoff/retry logic.

        Args:
            request_retries: The number of retries to give a failed request.

        Returns:
            A version of the request callable that can do retries.
        """
        return cast(
            Callable,
            backoff.on_exception(
                backoff.expo,
                ClientResponseError,
                giveup=self.is_fatal_error,  # type: ignore[arg-type]
                jitter=backoff.random_jitter,
                logger=LOGGER,
                max_tries=request_retries,
                on_backoff=self._async_handle_on_backoff,  # type: ignore[arg-type]
                on_giveup=self._handle_on_giveup,  # type: ignore[arg-type]
            )(self._async_api_request),
        )

    def disable_request_retries(self) -> None:
        """Disable the request retry mechanism."""
        self.async_request = self._wrap_request_method(1)

    def enable_request_retries(self) -> None:
        """Enable the request retry mechanism."""
        self.async_request = self._wrap_request_method(self._request_retries)

    def add_refresh_token_callback(
        self, callback: Callable[[str], Awaitable[None] | None]
    ) -> Callable[[], None]:
        """Add a callback that should be triggered when tokens are refreshed.

        Note that callbacks should expect to receive a refresh token as a parameter.

        Args:
            callback: The callback to execute.

        Returns:
            A callable to cancel the callback.
        """
        self._refresh_token_callbacks.append(callback)

        def remove() -> None:
            """Remove the callback."""
            self._refresh_token_callbacks.remove(callback)

        return remove

    async def async_get_systems(self) -> dict[int, SystemV2 | SystemV3]:
        """Get systems associated to the associated SimpliSafe account.

        In the dict that is returned, the keys are the subscription ID and the values
        are actual ``System`` objects.

        Returns:
            A dictionary of system IDs to System objects.
        """
        systems: dict[int, SystemV2 | SystemV3] = {}

        await self.async_update_subscription_data()

        for sid, subscription in self.subscription_data.items():
            if subscription["activated"] == 0 or not subscription["status"]["isActive"]:
                LOGGER.info("Skipping inactive subscription: %s", sid)
                continue

            if not subscription["location"].get("system"):
                LOGGER.error("Skipping subscription with missing system data: %s", sid)
                continue

            system: SystemV2 | SystemV3
            if subscription["location"]["system"]["version"] == 2:
                system = SystemV2(self, sid)
            else:
                system = SystemV3(self, sid)

            # Update the system, but don't include subscription data itself, since it
            # will already have been fetched when the API was first queried:
            await system.async_update(include_subscription=False)
            system.generate_device_objects()
            systems[sid] = system

        return systems

    async def async_refresh_access_token(self) -> None:
        """Initiate a refresh of the access/refresh tokens.

        Note that this will execute any callbacks added via add_refresh_token_callback.

        Raises:
            InvalidCredentialsError: Raised on invalid username/password.
            RequestError: Raised on general HTTP error.
            SimplipyError: Raised on an unknown error.
        """
        try:
            token_data = await self._async_api_request(
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
            if err.status in (401, 403):
                raise InvalidCredentialsError("Invalid refresh token") from err
            raise RequestError(
                f"Request error while attempting to refresh access token: {err}"
            ) from err
        except Exception as err:  # pylint: disable-broad-except
            raise SimplipyError(
                f"Error while attempting to refresh access token: {err}"
            ) from err

        self._save_token_data_from_response(token_data)

        for callback in self._refresh_token_callbacks:
            execute_callback(callback, self.refresh_token)

    async def async_update_subscription_data(self) -> None:
        """Get the latest subscription data."""
        subscription_resp = await self.async_request(
            "get", f"users/{self.user_id}/subscriptions", params={"activeOnly": "true"}
        )
        self.subscription_data = {
            subscription["sid"]: subscription
            for subscription in subscription_resp["subscriptions"]
        }
