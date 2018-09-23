"""Define tests for the System object."""
import json
from datetime import datetime, timedelta

import aiohttp
import aresponses
import pytest

from simplipy import get_systems
from simplipy.account import SimpliSafe
from simplipy.errors import RequestError, TokenExpiredError
from simplipy.system import System, SystemStates

from .const import (
    TEST_ACCESS_TOKEN, TEST_EMAIL, TEST_PASSWORD, TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID, TEST_SYSTEM_ID, TEST_SYSTEM_SERIAL_NO, TEST_USER_ID)
from .fixtures import *
from .fixtures.v2 import *
from .fixtures.v3 import *


@pytest.mark.asyncio
async def test_bad_request(api_token_json, event_loop, v2_server):
    """Test that a generic error is thrown when a request fails."""
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
async def test_get_events(events_json, event_loop, v2_server):
    """Test getting events from a system."""
    async with v2_server:
        v2_server.add(
            'api.simplisafe.com',
            '/v1/subscriptions/{0}/events'.format(TEST_SYSTEM_ID), 'get',
            aresponses.Response(text=json.dumps(events_json), status=200))

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            events = await system.get_events(1534725051, 2)
            assert len(events) == 2


@pytest.mark.asyncio
async def test_get_systems_v2(event_loop, v2_server):
    """Test the ability to get systems attached to a v2 account."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            systems = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            assert len(systems) == 1

            primary_system = systems[0]
            assert primary_system.serial == TEST_SYSTEM_SERIAL_NO
            assert primary_system.system_id == TEST_SYSTEM_ID
            assert primary_system.account.access_token == TEST_ACCESS_TOKEN
            assert len(primary_system.sensors) == 34


@pytest.mark.asyncio
async def test_get_systems_v3(event_loop, v3_server):
    """Test the ability to get systems attached to a v3 account."""
    async with v3_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            systems = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            assert len(systems) == 1

            primary_system = systems[0]
            assert primary_system.serial == TEST_SYSTEM_SERIAL_NO
            assert primary_system.system_id == TEST_SYSTEM_ID
            assert primary_system.account.access_token == TEST_ACCESS_TOKEN
            assert len(primary_system.sensors) == 21


@pytest.mark.asyncio
async def test_properties_base(event_loop, v2_server):
    """Test that base system properties are created properly."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            assert not system.alarm_going_off
            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.state == SystemStates.off
            assert system.system_id == TEST_SYSTEM_ID
            assert system.version == 2


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


@pytest.mark.asyncio
async def test_set_states_v2(
        event_loop, v2_server, v2_state_away_json, v2_state_home_json,
        v2_state_off_json):
    """Test the ability to set the state of a v2 system."""
    async with v2_server:
        # Since this flow will make the same API call four times and
        # aresponses deletes matches each time, we need to add four additional
        # routes:
        v2_server.add(
            'api.simplisafe.com',
            '/v1/subscriptions/{0}/state'.format(TEST_SUBSCRIPTION_ID), 'post',
            aresponses.Response(
                text=json.dumps(v2_state_away_json), status=200))
        v2_server.add(
            'api.simplisafe.com',
            '/v1/subscriptions/{0}/state'.format(TEST_SUBSCRIPTION_ID), 'post',
            aresponses.Response(
                text=json.dumps(v2_state_home_json), status=200))
        v2_server.add(
            'api.simplisafe.com',
            '/v1/subscriptions/{0}/state'.format(TEST_SUBSCRIPTION_ID), 'post',
            aresponses.Response(
                text=json.dumps(v2_state_off_json), status=200))
        v2_server.add(
            'api.simplisafe.com',
            '/v1/subscriptions/{0}/state'.format(TEST_SUBSCRIPTION_ID), 'post',
            aresponses.Response(
                text=json.dumps(v2_state_off_json), status=200))

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            await system.set_away()
            assert system.state == SystemStates.away

            await system.set_home()
            assert system.state == SystemStates.home

            await system.set_off()
            assert system.state == SystemStates.off

            await system.set_off()
            assert system.state == SystemStates.off


@pytest.mark.asyncio
async def test_set_states_v3(
        event_loop, v3_server, v3_state_away_json, v3_state_home_json,
        v3_state_off_json):
    """Test the ability to set the state of the system."""
    async with v3_server:
        # Since this flow will make the same API call four times and
        # aresponses deletes matches each time, we need to add four additional
        # routes:
        v3_server.add(
            'api.simplisafe.com', '/v1/ss3/subscriptions/{0}/state/{1}'.format(
                TEST_SUBSCRIPTION_ID, SystemStates.away.name), 'post',
            aresponses.Response(
                text=json.dumps(v3_state_away_json), status=200))
        v3_server.add(
            'api.simplisafe.com', '/v1/ss3/subscriptions/{0}/state/{1}'.format(
                TEST_SUBSCRIPTION_ID, SystemStates.home.name), 'post',
            aresponses.Response(
                text=json.dumps(v3_state_home_json), status=200))
        v3_server.add(
            'api.simplisafe.com', '/v1/ss3/subscriptions/{0}/state/{1}'.format(
                TEST_SUBSCRIPTION_ID, SystemStates.off.name), 'post',
            aresponses.Response(
                text=json.dumps(v3_state_off_json), status=200))
        v3_server.add(
            'api.simplisafe.com', '/v1/ss3/subscriptions/{0}/state/{1}'.format(
                TEST_SUBSCRIPTION_ID, SystemStates.off.name), 'post',
            aresponses.Response(
                text=json.dumps(v3_state_off_json), status=200))

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            await system.set_away()
            assert system.state == SystemStates.away

            await system.set_home()
            assert system.state == SystemStates.home

            await system.set_off()
            assert system.state == SystemStates.off

            await system.set_off()
            assert system.state == SystemStates.off


@pytest.mark.asyncio
async def test_unknown_initial_state(caplog, event_loop):
    """Test handling of an initially unknown state."""
    async with aiohttp.ClientSession(loop=event_loop) as websession:
        _ = System(
            SimpliSafe(websession), {'system': {
                'alarmState': 'fake'
            }})

        assert any('Unknown' in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_unknown_sensor_type(caplog, event_loop, v2_server):
    """Test getting a new access token from a refresh token."""
    async with v2_server:
        async with aiohttp.ClientSession(loop=event_loop) as websession:
            await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)
            assert any('Unknown' in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_update_system_data_v2(
        event_loop, v2_server, v2_settings_json, v2_subscriptions_json):
    """Test getting updated data for a v2 system."""
    async with v2_server:
        v2_server.add(
            'api.simplisafe.com',
            '/v1/users/{0}/subscriptions'.format(TEST_USER_ID), 'get',
            aresponses.Response(
                text=json.dumps(v2_subscriptions_json), status=200))
        v2_server.add(
            'api.simplisafe.com',
            '/v1/subscriptions/{0}/settings'.format(TEST_SUBSCRIPTION_ID),
            'get',
            aresponses.Response(text=json.dumps(v2_settings_json), status=200))

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            await system.update()
            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert system.account.access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 34


@pytest.mark.asyncio
async def test_update_system_data_v3(
        event_loop, v3_server, v3_sensors_json, v3_subscriptions_json):
    """Test getting updated data for a v3 system."""
    async with v3_server:
        v3_server.add(
            'api.simplisafe.com',
            '/v1/users/{0}/subscriptions'.format(TEST_USER_ID), 'get',
            aresponses.Response(
                text=json.dumps(v3_subscriptions_json), status=200))
        v3_server.add(
            'api.simplisafe.com',
            '/v1/ss3/subscriptions/{0}/sensors'.format(TEST_SUBSCRIPTION_ID),
            'get',
            aresponses.Response(text=json.dumps(v3_sensors_json), status=200))

        async with aiohttp.ClientSession(loop=event_loop) as websession:
            [system] = await get_systems(TEST_EMAIL, TEST_PASSWORD, websession)

            await system.update()
            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert system.account.access_token == TEST_ACCESS_TOKEN
            assert len(system.sensors) == 21
