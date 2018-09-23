"""Define tests for the System object."""
import json
from datetime import datetime, timedelta

import aiohttp
import aresponses
import pytest

from simplipy import get_systems
from simplipy.errors import RequestError, TokenExpiredError

from .const import (
    TEST_ACCESS_TOKEN, TEST_EMAIL, TEST_PASSWORD, TEST_REFRESH_TOKEN,
    TEST_SYSTEM_ID, TEST_SYSTEM_SERIAL_NO)
from .fixtures import *
from .fixtures.v2 import *
from .fixtures.v3 import *


@pytest.mark.asyncio
async def test_bad_request(api_token_json, event_loop, v2_server):
    """Test that the correct exception is raised when the token is expired."""
    async with v2_server:
        v2_server.add(
            'api.simplisafe.com', '/v1/api/fakeEndpoint', 'get',
            aresponses.Response(text='', status=404))

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            with pytest.raises(RequestError):
                await system.account.request('get', 'api/fakeEndpoint')


@pytest.mark.asyncio
async def test_expired_token_exception(event_loop, v2_server):
    """Test that the correct exception is raised when the token is expired."""
    async with v2_server:
        v2_server.add(
            'api.simplisafe.com', '/v1/api/authCheck', 'get',
            aresponses.Response(text='', status=401))

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            system.account._access_token_expire = datetime.now() - timedelta(
                hours=1)

            with pytest.raises(TokenExpiredError):
                await system.account.request('get', 'api/authCheck')


@pytest.mark.asyncio
async def test_get_systems_v2(event_loop, v2_server):
    """Test the ability to get systems attached to an account."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            systems = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            assert len(systems) == 1

            primary_system = systems[0]
            assert primary_system.serial_number == TEST_SYSTEM_SERIAL_NO
            assert primary_system.system_id == TEST_SYSTEM_ID
            assert primary_system.account.access_token == TEST_ACCESS_TOKEN
            assert len(primary_system.sensors) == 34


@pytest.mark.asyncio
async def test_get_systems_v3(event_loop, v3_server):
    """Test the ability to get systems attached to an account."""
    async with v3_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            systems = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            assert len(systems) == 1

            primary_system = systems[0]
            assert primary_system.serial_number == TEST_SYSTEM_SERIAL_NO
            assert primary_system.system_id == TEST_SYSTEM_ID
            assert primary_system.account.access_token == TEST_ACCESS_TOKEN
            assert len(primary_system.sensors) == 21


@pytest.mark.asyncio
async def test_refresh_token(api_token_json, event_loop, v2_server):
    """Test getting a new access token from a refresh token."""
    async with v2_server:
        # Since this flow will call /v1/api/token twice more (on top of what
        # instantiation does) and aresponses deletes matches each time, we need
        # to add two additional routes:
        v2_server.add(
            'api.simplisafe.com', '/v1/api/token', 'post',
            aresponses.Response(text=json.dumps(api_token_json), status=200))
        v2_server.add(
            'api.simplisafe.com', '/v1/api/token', 'post',
            aresponses.Response(text=json.dumps(api_token_json), status=200))

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            await system.account.refresh_access_token()
            assert system.account.access_token == TEST_ACCESS_TOKEN

            await system.account.refresh_access_token(TEST_REFRESH_TOKEN)
            assert system.account.access_token == TEST_ACCESS_TOKEN
