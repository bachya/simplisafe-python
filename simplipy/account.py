"""Define a SimpliSafe account."""
from datetime import datetime, timedelta
from typing import List, Union

from aiohttp import BasicAuth, ClientSession, client_exceptions

from .errors import RequestError, TokenExpiredError
from .system import System, SystemV2, SystemV3

DEFAULT_USER_AGENT = 'SimpliSafe/2105 CFNetwork/902.2 Darwin/17.7.0'
DEFAULT_AUTH_USERNAME = 'a9c490a5-28c7-48c8-a8c3-1f1d7faa1394.2074.0.0.com.' \
    'simplisafe.mobile'

URL_HOSTNAME = 'api.simplisafe.com'
URL_BASE = 'https://{0}/v1'.format(URL_HOSTNAME)

SYSTEM_MAP = {
    2: SystemV2,
    3: SystemV3
}


# pylint: disable=protected-access
async def get_systems(
        email: str, password: str, websession: ClientSession) -> list:
    """Return a list of systems."""
    account = SimpliSafe(websession)
    await account._login(email, password)
    return await account._get_subscriptions()


class SimpliSafe:
    """Define an "account" client."""

    def __init__(self, websession: ClientSession) -> None:
        """Initialize."""
        self._access_token_expire = None  # type: Union[None, datetime]
        self._email = None  # type: Union[None, str]
        self._websession = websession
        self.access_token = None
        self.refresh_token = None
        self.user_id = None

    async def _authenticate(self, payload_data: dict) -> None:
        """Request token data and parse it."""
        token_resp = await self.request(
            'post',
            'api/token',
            data=payload_data,
            auth=BasicAuth(DEFAULT_AUTH_USERNAME))
        self.access_token = token_resp['access_token']
        self._access_token_expire = datetime.now() + timedelta(
            seconds=int(token_resp['expires_in']))
        self.refresh_token = token_resp['refresh_token']

    async def _get_subscriptions(self) -> list:
        """Get subscriptions associated to this account."""
        subscription_resp = await self.get_subscription_data()

        systems = []  # type: List[System]
        for system_data in subscription_resp['subscriptions']:
            version = system_data['location']['system']['version']
            system_class = SYSTEM_MAP[version]
            system = system_class(self, system_data['location'])
            await system.update(refresh_location=False)
            systems.append(system)

        return systems

    async def _login(self, email: str, password: str) -> None:
        """Login to SimpliSafe."""
        self._email = email

        await self._authenticate({
            'grant_type': 'password',
            'username': email,
            'password': password,
        })

        auth_check_resp = await self.request('get', 'api/authCheck')
        self.user_id = auth_check_resp['userId']

    async def get_subscription_data(self) -> dict:
        """Get the latest location-level data."""
        return await self.request(
            'get',
            'users/{0}/subscriptions'.format(self.user_id),
            params={'activeOnly': 'true'})

    async def refresh_access_token(self, refresh_token: str = None) -> None:
        """Regenerate an access token using the stored refresh token."""
        await self._authenticate({
            'grant_type': 'refresh_token',
            'username': self._email,
            'refresh_token':
                refresh_token if refresh_token else self.refresh_token,
        })

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
            raise TokenExpiredError('The access token has expired')

        url = '{0}/{1}'.format(URL_BASE, endpoint)

        if not headers:
            headers = {}
        if not kwargs.get('auth') and self.access_token:
            headers['Authorization'] = 'Bearer {0}'.format(self.access_token)
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': URL_HOSTNAME,
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
