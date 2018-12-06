"""Define a SimpliSafe account."""
# pylint: disable=import-error,protected-access,too-many-instance-attributes
# pylint: disable=unused-import

import logging
from datetime import datetime, timedelta
from typing import List, Type, TypeVar, Union  # noqa
from uuid import uuid4

from aiohttp import BasicAuth, ClientSession
from aiohttp.client_exceptions import ClientError

from .errors import InvalidCredentialsError, RequestError
from .system import System, SystemV2, SystemV3  # noqa

_LOGGER = logging.getLogger(__name__)

DEFAULT_USER_AGENT = 'SimpliSafe/2105 CFNetwork/902.2 Darwin/17.7.0'
DEFAULT_AUTH_USERNAME = '{0}.2074.0.0.com.simplisafe.mobile'

SYSTEM_MAP = {2: SystemV2, 3: SystemV3}

URL_HOSTNAME = 'api.simplisafe.com'
URL_BASE = 'https://{0}/v1'.format(URL_HOSTNAME)

ApiType = TypeVar('ApiType', bound='API')


class API:
    """Define an API object to interact with the SimpliSafe cloud."""

    def __init__(self, websession: ClientSession) -> None:
        """Initialize."""
        self._access_token = ''
        self._access_token_expire = None  # type: Union[None, datetime]
        self._actively_refreshing = False
        self._email = None  # type: Union[None, str]
        self._refresh_token = ''
        self._uuid = uuid4()
        self._websession = websession
        self.refresh_token_dirty = False
        self.user_id = None

    @property
    def refresh_token(self) -> str:
        """Return the current refresh_token."""
        if self.refresh_token_dirty:
            self.refresh_token_dirty = False

        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: str) -> None:
        """Set the refresh token if it has changed."""
        if value == self._refresh_token:
            return

        self._refresh_token = value
        self.refresh_token_dirty = True

    @classmethod
    async def login_via_credentials(
            cls: Type[ApiType], email: str, password: str,
            websession: ClientSession) -> ApiType:
        """Create an API object from a email address and password."""
        klass = cls(websession)
        klass._email = email

        await klass._authenticate({
            'grant_type': 'password',
            'username': email,
            'password': password,
        })

        return klass

    @classmethod
    async def login_via_token(
            cls: Type[ApiType], refresh_token: str,
            websession: ClientSession) -> ApiType:
        """Create an API object from a refresh token."""
        klass = cls(websession)
        await klass._refresh_access_token(refresh_token)
        return klass

    async def _authenticate(self, payload_data: dict) -> None:
        """Request token data and parse it."""
        token_resp = await self.request(
            'post',
            'api/token',
            data=payload_data,
            auth=BasicAuth(
                login=DEFAULT_AUTH_USERNAME.format(self._uuid),
                password='',
                encoding='latin1'))

        self._access_token = token_resp['access_token']
        self._access_token_expire = datetime.now() + timedelta(
            seconds=int(token_resp['expires_in']) - 60)
        self.refresh_token = token_resp['refresh_token']

        auth_check_resp = await self.request('get', 'api/authCheck')
        self.user_id = auth_check_resp['userId']

    async def _refresh_access_token(self, refresh_token: str) -> None:
        """Regenerate an access token."""
        await self._authenticate({
            'grant_type': 'refresh_token',
            'username': self._email,
            'refresh_token': refresh_token,
        })

        self._actively_refreshing = False

    async def get_systems(self) -> list:
        """Get systems associated to this account."""
        subscription_resp = await self.get_subscription_data()

        systems = []  # type: List[System]
        for system_data in subscription_resp['subscriptions']:
            version = system_data['location']['system']['version']
            system_class = SYSTEM_MAP[version]
            system = system_class(self, system_data['location'])
            await system.update(refresh_location=False)
            systems.append(system)

        return systems

    async def get_subscription_data(self) -> dict:
        """Get the latest location-level data."""
        subscription_resp = await self.request(
            'get',
            'users/{0}/subscriptions'.format(self.user_id),
            params={'activeOnly': 'true'})

        _LOGGER.debug('Subscription response: %s', subscription_resp)

        return subscription_resp

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
                and datetime.now() >= self._access_token_expire
                and not self._actively_refreshing):
            self._actively_refreshing = True
            await self._refresh_access_token(self._refresh_token)

        url = '{0}/{1}'.format(URL_BASE, endpoint)

        if not headers:
            headers = {}
        if not kwargs.get('auth') and self._access_token:
            headers['Authorization'] = 'Bearer {0}'.format(self._access_token)
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': URL_HOSTNAME,
            'User-Agent': DEFAULT_USER_AGENT,
        })

        try:
            async with self._websession.request(method, url, headers=headers,
                                                params=params, data=data,
                                                json=json, **kwargs) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except ClientError as err:
            if self.user_id and '403' in str(err):
                _LOGGER.info(
                    'Endpoint not available in this plan: %s', endpoint)
                return {}
            if not self.user_id and '403' in str(err):
                raise InvalidCredentialsError

            raise RequestError(
                'Error requesting data from {0}: {1}'.format(endpoint, err))
