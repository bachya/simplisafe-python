"""Define base tests for System objects."""
from datetime import datetime

import aiohttp
import pytest

from simplipy import API
from simplipy.system import SystemStates

from tests.common import (
    TEST_ADDRESS,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    load_fixture,
)


@pytest.mark.asyncio
async def test_get_events(aresponses, v2_server):
    """Test getting events from a system."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SYSTEM_ID}/events",
            "get",
            aresponses.Response(text=load_fixture("events_response.json"), status=200),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            events = await system.get_events(datetime.now(), 2)

            assert len(events) == 2


@pytest.mark.asyncio
async def test_get_events_no_explicit_session(aresponses, v2_server):
    """Test getting events from a system without an explicit aiohttp ClientSession."""
    async with v2_server:
        v2_server.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SYSTEM_ID}/events",
            "get",
            aresponses.Response(text=load_fixture("events_response.json"), status=200),
        )

        simplisafe = await API.login_via_credentials(TEST_EMAIL, TEST_PASSWORD)
        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        events = await system.get_events(datetime.now(), 2)

        assert len(events) == 2


@pytest.mark.asyncio
async def test_properties(v2_server):
    """Test that base system properties are created properly."""
    async with v2_server:
        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            systems = await simplisafe.get_systems()
            system = systems[TEST_SYSTEM_ID]

            assert not system.alarm_going_off
            assert system.address == TEST_ADDRESS
            assert system.connection_type == "wifi"
            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.state == SystemStates.off
            assert system.system_id == TEST_SYSTEM_ID
            assert system.temperature == 67
            assert system.version == 2


@pytest.mark.asyncio
async def test_unknown_sensor_type(caplog, v2_server):
    """Test whether a message is logged upon finding an unknown sensor type."""
    async with v2_server:
        async with aiohttp.ClientSession() as session:
            simplisafe = await API.login_via_credentials(
                TEST_EMAIL, TEST_PASSWORD, session=session
            )
            _ = await simplisafe.get_systems()
            assert any("Unknown" in e.message for e in caplog.records)
