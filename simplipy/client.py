"""Define a client to interact with Pollen.com."""
from datetime import datetime, timedelta
from typing import List, Union

from aiohttp import BasicAuth, ClientSession, client_exceptions

from .errors import RequestError, TokenExpiredError
from .system import System

DEFAULT_USER_AGENT = 'SimpliSafe/2105 CFNetwork/902.2 Darwin/17.7.0'
DEFAULT_AUTH_USERNAME = 'a9c490a5-28c7-48c8-a8c3-1f1d7faa1394.2074.0.0.com.' \
    'simplisafe.mobile'

HOSTNAME = 'api.simplisafe.com'
URL_BASE = 'https://{0}/v1'.format(HOSTNAME)


class Client:
    """Define the client."""

    def __init__(self, email: str, websession: ClientSession) -> None:
        """Initialize."""
        self._access_token = None
        self._access_token_expire = None  # type: Union[None, datetime]
        self._email = email
        self._refresh_token = None
        self._websession = websession
        self.systems = []  # type: List[System]
        self.user_id = None

    async def _authenticate(self, payload_data: dict) -> None:
        """Request token data and parse it."""

        # Process access and refresh tokens:
        token_resp = await self.request(
            'post',
            'api/token',
            data=payload_data,
            auth=BasicAuth(DEFAULT_AUTH_USERNAME))
        self._access_token = token_resp['access_token']
        self._access_token_expire = datetime.now() + timedelta(
            seconds=int(token_resp['expires_in']))
        self._refresh_token = token_resp['refresh_token']

        # Process the user ID:
        auth_check_resp = await self.request('get', 'api/authCheck')
        self.user_id = auth_check_resp['userId']

        # Retrieve the systems assigned to this user:
        sub_resp = await self.request(
            'get',
            'users/{0}/subscriptions'.format(self.user_id),
            params={'activeOnly': 'true'})
        for system in sub_resp.get('subscriptions', []):
            self.systems.append(System(self, system['location']))

    async def request(
            self,
            method: str,
            endpoint: str,
            *,
            headers: dict = None,
            params: dict = None,
            data: dict = None,
            json: dict = None,
            **kwargs) -> dict:
        """Make a request."""
        if (self._access_token_expire
                and datetime.now() >= self._access_token_expire):
            raise TokenExpiredError('Please create a new token')

        url = '{0}/{1}'.format(URL_BASE, endpoint)

        if not headers:
            headers = {}
        if self._access_token:
            headers['Authorization'] = 'Bearer {0}'.format(self._access_token)
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': HOSTNAME,
            'User-Agent': DEFAULT_USER_AGENT,
        })

        async with self._websession.request(method, url, headers=headers,
                                            params=params, data=data,
                                            json=json, **kwargs) as resp:
            try:
                resp.raise_for_status()
                return await resp.json(content_type=None)
            except client_exceptions.ClientError as err:
                raise RequestError(
                    'Error requesting data from {0}: {1}'.format(
                        endpoint, err)) from None

    async def authenticate_password(self, password: str) -> None:
        """Authenticate with a password."""
        await self._authenticate({
            'grant_type': 'password',
            'username': self._email,
            'password': password,
        })

    async def authenticate_refresh_token(
            self, refresh_token: str = None) -> None:
        """Authenticate with a refresh token."""
        if not refresh_token and not self._refresh_token:
            raise ValueError('No valid refresh token given')

        await self._authenticate({
            'grant_type': 'refresh_token',
            'username': self._email,
            'refresh_token':
                refresh_token if refresh_token else self._refresh_token,
        })
