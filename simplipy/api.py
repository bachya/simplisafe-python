"""Define functionality for interacting with the SimpliSafe API."""
from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from json.decoder import JSONDecodeError
import sys
from typing import Any, Callable, cast

from aiohttp import ClientResponse, ClientSession
from aiohttp.client_exceptions import ClientResponseError
import backoff
from bs4 import BeautifulSoup
from yarl import URL

from simplipy.const import DEFAULT_USER_AGENT, LOGGER
from simplipy.errors import (
    InvalidCredentialsError,
    RequestError,
    SimplipyError,
    Verify2FAError,
    Verify2FAPending,
    raise_on_data_error,
)
from simplipy.system.v2 import SystemV2
from simplipy.system.v3 import SystemV3
from simplipy.util import execute_callback
from simplipy.util.auth import get_auth0_code_challenge, get_auth0_code_verifier
from simplipy.websocket import WebsocketClient

API_URL_HOSTNAME = "api.simplisafe.com"
API_URL_BASE = f"https://{API_URL_HOSTNAME}/v1"

AUTH_URL_HOSTNAME = "auth.simplisafe.com"
AUTH_URL_BASE = f"https://{AUTH_URL_HOSTNAME}"

DEFAULT_AUTH0_CLIENT = (
    "eyJuYW1lIjoiQXV0aDAuc3dpZnQiLCJlbnYiOnsiaU"
    "9TIjoiMTUuMCIsInN3aWZ0IjoiNS54In0sInZlcnNpb24iOiIxLjMzLjAifQ"
)
DEFAULT_CLIENT_ID = "42aBZ5lYrVW12jfOuu3CQROitwxg9sN5"
DEFAULT_REDIRECT_URI = (
    "com.simplisafe.mobile://auth.simplisafe.com/ios/com.simplisafe.mobile/callback"
)
DEFAULT_REQUEST_RETRIES = 4
DEFAULT_SCOPE = (
    "offline_access email openid https://api.simplisafe.com/scopes/user:platform"
)
DEFAULT_TIMEOUT = 10
DEFAULT_TOKEN_EXPIRATION_WINDOW = 5


class AuthStates(Enum):
    """Define an API object authenticate state."""

    UNAUTHENTICATED = 0
    PENDING_2FA_EMAIL = 1
    PENDING_2FA_SMS = 2
    AUTHENTICATED = 3


class API:  # pylint: disable=too-many-instance-attributes
    """Define an API object to interact with the SimpliSafe cloud.

    Note that this class shouldn't be instantiated directly; instead, the
    :meth:`simplipy.api.API.async_from_credentials` and
    :meth:`simplipy.api.API.async_from_refresh_token` methods should be used.

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
        self._refresh_token_callbacks: list[Callable[..., None]] = []
        self._request_retries = request_retries
        self.session: ClientSession = session

        # These will get filled in after initial authentication:
        self._backoff_refresh_lock = asyncio.Lock()
        self._code_verifier: str = get_auth0_code_verifier()
        self._login_verification_url: URL | None = None
        self._token_last_refreshed: datetime | None = None
        self.access_token: str | None = None
        self.auth_state: AuthStates = AuthStates.UNAUTHENTICATED
        self.refresh_token: str | None = None
        self.subscription_data: dict[int, Any] = {}
        self.user_id: int | None = None
        self.websocket: WebsocketClient | None = None

        self.async_request = self._wrap_request_method(self._request_retries)

    @classmethod
    async def async_from_credentials(
        cls,
        username: str,
        password: str,
        *,
        session: ClientSession,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
    ) -> API:
        """Get an authenticated API object from a username and password.

        :param username: A SimpliSafe account username/email address
        :type username: ``str``
        :param pswd: A SimpliSafe account password
        :type pswd: ``str``
        :param session: An ``aiohttp`` ``ClientSession``
        :type session: ``aiohttp.client.ClientSession``
        :param request_retries: The default number of request retries to use
        :type request_retries: ``int``
        :rtype: :meth:`simplipy.api.API`
        """
        api = cls(session=session, request_retries=request_retries)

        # Generate a SimpliSafe Auth0 auth URL:
        code_challenge = get_auth0_code_challenge(api._code_verifier)

        # Determine the login URL:
        try:
            auth0_resp = await session.request(
                "get",
                f"{AUTH_URL_BASE}/authorize",
                allow_redirects=False,
                headers={
                    "Accept": "text/html",
                    "User-Agent": DEFAULT_USER_AGENT,
                },
                params={
                    "audience": f"https://{API_URL_HOSTNAME}/",
                    "auth0Client": DEFAULT_AUTH0_CLIENT,
                    "client_id": DEFAULT_CLIENT_ID,
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                    "redirect_uri": DEFAULT_REDIRECT_URI,
                    "response_mode": "query",
                    "response_type": "code",
                    "scope": DEFAULT_SCOPE,
                },
            )
            auth0_resp.raise_for_status()
        except Exception as err:  # pylint: disable-broad-except
            raise SimplipyError(
                f"Error while determining the Auth0 login URL: {err}"
            ) from err

        LOGGER.debug("Auth0 response headers: %s", auth0_resp.headers)

        if not auth0_resp.headers["Location"].startswith("/"):
            # Login has already occurred (according to the session cookies we have), so
            # we already have the login verification URL:
            api._login_verification_url = URL(auth0_resp.headers["Location"])
        else:
            # Attempt to login:
            login_resp = await session.request(
                "post",
                f"{AUTH_URL_BASE}{auth0_resp.headers['Location']}",
                data={
                    "password": password,
                    "username": username,
                },
            )

            body = await login_resp.text()
            LOGGER.debug("Login attempt response body: %s", body)

            if "invalid_user_password" in body:
                raise InvalidCredentialsError("Invalid username/password")
            if "too-many-sms" in body:
                raise Verify2FAError("SMS 2FA limit per hour exceeded; try again later")

            api._login_verification_url = login_resp.url

        LOGGER.debug("API Verification URL: %s", api._login_verification_url)
        assert api._login_verification_url

        # From what we can tell, SimpliSAfe requires 2FA on all accounts; unless we can
        # detect a more specific method, assume the user is using email-based 2FA:
        if "mfa-sms-challenge" in str(api._login_verification_url):
            api.auth_state = AuthStates.PENDING_2FA_SMS
        else:
            api.auth_state = AuthStates.PENDING_2FA_EMAIL

        # At the stage, the API object is created, but is not ready to be used until
        # 2FA is resolved:
        return api

    @classmethod
    async def async_from_refresh_token(
        cls,
        refresh_token: str,
        *,
        session: ClientSession,
        request_retries: int = DEFAULT_REQUEST_RETRIES,
    ) -> API:
        """Get an authenticated API object from a refresh token.

        :param refresh_token: The refresh token
        :type refresh_token: ``str``
        :param session: An ``aiohttp`` ``ClientSession``
        :type session: ``aiohttp.client.ClientSession``
        :param request_retries: The default number of request retries to use
        :type request_retries: ``int``
        :rtype: :meth:`simplipy.api.API`
        """
        api = cls(session=session, request_retries=request_retries)
        api.refresh_token = refresh_token
        await api.async_refresh_access_token()
        await api._async_post_init()
        return api

    async def _async_complete_login(
        self, login_verification_resp: ClientResponse
    ) -> None:
        """Complete the login process after 2FA verification."""
        try:
            auth_resume_resp = await self.session.request(
                "get",
                f"{AUTH_URL_BASE}{login_verification_resp.headers['Location']}",
                allow_redirects=False,
            )
            auth_resume_resp.raise_for_status()
        except Exception as err:  # pylint: disable-broad-except
            raise SimplipyError(
                f"Error while attempting to get authorization code: {err}"
            ) from err

        auth_code_url = URL(auth_resume_resp.headers["Location"])
        LOGGER.debug("Auth Code URL: %s", auth_code_url)
        auth_code = auth_code_url.query["code"]

        try:
            token_resp = await self.session.request(
                "post",
                f"{AUTH_URL_BASE}/oauth/token",
                json={
                    "grant_type": "authorization_code",
                    "client_id": DEFAULT_CLIENT_ID,
                    "code_verifier": self._code_verifier,
                    "code": auth_code,
                    "redirect_uri": DEFAULT_REDIRECT_URI,
                },
            )
            token_resp.raise_for_status()
        except Exception as err:  # pylint: disable-broad-except
            raise SimplipyError(
                f"Unknown error while attempting getting access token: {err}"
            ) from err

        await self._async_save_token_data_from_response(token_resp)
        await self._async_post_init()

    async def _async_handle_on_backoff(self, _: dict[str, Any]) -> None:
        """Handle a backoff retry."""
        err_info = sys.exc_info()
        err: ClientResponseError = err_info[1].with_traceback(  # type: ignore
            err_info[2]
        )

        LOGGER.debug("Error during request attempt: %s", err)

        if err.status == 401:
            assert self._token_last_refreshed

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
        self.auth_state = AuthStates.AUTHENTICATED
        auth_check_resp = await self._async_api_request("get", "api/authCheck")
        self.user_id = auth_check_resp["userId"]
        self.websocket = WebsocketClient(self)

    async def _async_api_request(
        self, method: str, endpoint: str, url_base: str = API_URL_BASE, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute an API request."""
        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault("Host", API_URL_HOSTNAME)
        kwargs["headers"]["Content-Type"] = "application/json; charset=utf-8"
        kwargs["headers"]["User-Agent"] = DEFAULT_USER_AGENT
        if self.access_token:
            kwargs["headers"]["Authorization"] = f"Bearer {self.access_token}"

        data: dict[str, Any] = {}
        async with self.session.request(
            method, f"{url_base}/{endpoint}", **kwargs
        ) as resp:
            try:
                data = await resp.json(content_type=None)
            except JSONDecodeError:
                message = await resp.text()
                data = {"type": "DataParsingError", "message": message}

            LOGGER.debug("Data received from /%s: %s", endpoint, data)

            raise_on_data_error(data)
            resp.raise_for_status()

        return data

    async def _async_save_token_data_from_response(
        self, token_resp: ClientResponse
    ) -> None:
        """Save token data from a token response."""
        token_data = await token_resp.json()
        self._token_last_refreshed = datetime.utcnow()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]

    @staticmethod
    def _handle_on_giveup(_: dict[str, Any]) -> None:
        """Handle a give up after retries are exhausted."""
        err_info = sys.exc_info()
        err = err_info[1].with_traceback(err_info[2])  # type: ignore
        raise RequestError(err) from err

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
        """
        assert isinstance(err.status, int)
        if err.status in (401, 409):
            return False
        return 400 <= err.status < 500

    def _wrap_request_method(self, request_retries: int) -> Callable:
        """Wrap the request method in backoff/retry logic."""
        return cast(
            Callable,
            backoff.on_exception(
                backoff.expo,
                ClientResponseError,
                giveup=self.is_fatal_error,
                jitter=backoff.random_jitter,
                logger=LOGGER,
                max_tries=request_retries,
                on_backoff=self._async_handle_on_backoff,
                on_giveup=self._handle_on_giveup,
            )(self._async_api_request),
        )

    def disable_request_retries(self) -> None:
        """Disable the request retry mechanism."""
        self.async_request = self._wrap_request_method(1)

    def enable_request_retries(self) -> None:
        """Enable the request retry mechanism."""
        self.async_request = self._wrap_request_method(self._request_retries)

    def add_refresh_token_callback(
        self, callback: Callable[..., Any]
    ) -> Callable[..., None]:
        """Add a callback that should be triggered when tokens are refreshed.

        Note that callbacks should expect to receive a refresh token as a parameter.

        :param callback: The method to call after receiving an event.
        :type callback: ``Callable[..., None]``
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

        :rtype: ``Dict[int, simplipy.system.System]``
        """
        systems: dict[int, SystemV2 | SystemV3] = {}

        await self.async_update_subscription_data()

        for sid, subscription in self.subscription_data.items():
            if not subscription["status"]["isActive"] != 0:
                LOGGER.info("Skipping inactive subscription: %s", sid)
                continue

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

    async def async_refresh_access_token(self) -> None:
        """Initiate a refresh of the access/refresh tokens.

        Note that this will execute any callbacks added via add_refresh_token_callback.
        """
        try:
            token_resp = await self.session.request(
                "post",
                f"{AUTH_URL_BASE}/oauth/token",
                json={
                    "grant_type": "refresh_token",
                    "client_id": DEFAULT_CLIENT_ID,
                    "refresh_token": self.refresh_token,
                },
            )
            token_resp.raise_for_status()
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

        await self._async_save_token_data_from_response(token_resp)

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

    async def async_verify_2fa_email(self) -> None:
        """Verify that email-based 2FA has succeeded and mark the API as ready."""
        if self.auth_state != AuthStates.PENDING_2FA_EMAIL:
            raise ValueError("API object is not awaiting email-based 2FA verification")

        login_check_resp = await self.session.request(
            "get", self._login_verification_url
        )
        body = await login_check_resp.text()
        LOGGER.debug("Email-based 2FA attempt response body: %s", body)

        if "Verification Pending" in body:
            raise Verify2FAPending("Email-based 2FA verification still pending")
        if "Verification Successful" not in body:
            raise Verify2FAError("Unknown error during email-based 2FA verification")

        login_check_soup = BeautifulSoup(body, "html.parser")
        login_token = login_check_soup.find("input", {"name": "token"})["value"]

        assert self._login_verification_url

        login_verification_resp = await self.session.request(
            "post",
            f"{AUTH_URL_BASE}/continue",
            allow_redirects=False,
            params={
                "state": self._login_verification_url.query["state"],
            },
            data={
                "token": login_token,
            },
        )

        LOGGER.debug(
            "Login Verification Response Headers: %s", login_verification_resp.headers
        )

        await self._async_complete_login(login_verification_resp)

    async def async_verify_2fa_sms(self, code: str) -> None:
        """Verify that email-based 2FA has been successful and mark the API as ready.

        :param code: An SMS 2FA code to try
        :type code: ``str``
        """
        if self.auth_state != AuthStates.PENDING_2FA_SMS:
            raise ValueError("API object is not awaiting SMS-based 2FA verification")

        login_verification_resp = await self.session.request(
            "post",
            self._login_verification_url,
            allow_redirects=False,
            data={"code": code},
        )

        body = await login_verification_resp.text()
        LOGGER.debug("SMS-based 2FA attempt response body: %s", body)

        if "invalid-code" in body:
            raise InvalidCredentialsError("Invalid SMS 2FA code")

        await self._async_complete_login(login_verification_resp)
