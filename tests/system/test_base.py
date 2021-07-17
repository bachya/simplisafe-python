"""Define base tests for System objects."""
# pylint: disable=unused-argument
from datetime import datetime
import re

import aiohttp
import pytest

from simplipy import get_api
from simplipy.system import SystemStates

from tests.common import (
    TEST_ADDRESS,
    TEST_CLIENT_ID,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    load_fixture,
)


@pytest.mark.parametrize(
    "v3_subscriptions_response",
    [load_fixture("subscriptions_deactivated_response.json")],
)
async def test_deactivated_system(v3_server):
    """Test that API.get_systems doesn't return deactivated systems."""
    simplisafe = await get_api(TEST_EMAIL, TEST_PASSWORD, client_id=TEST_CLIENT_ID)

    systems = await simplisafe.get_systems()

    assert len(systems) == 0


async def test_get_events(v3_server):
    """Test getting events from a system."""
    v3_server.get(
        re.compile(
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SYSTEM_ID}/events.+"
        ),
        status=200,
        body=load_fixture("events_response.json"),
    )

    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        events = await system.get_events(datetime.now(), 2)

        assert len(events) == 2


async def test_get_events_no_explicit_session(v3_server):
    """Test getting events from a system without an explicit aiohttp ClientSession."""
    v3_server.get(
        re.compile(
            f"https://api.simplisafe.com/v1/subscriptions/{TEST_SYSTEM_ID}/events.+"
        ),
        status=200,
        body=load_fixture("events_response.json"),
    )

    simplisafe = await get_api(TEST_EMAIL, TEST_PASSWORD, client_id=TEST_CLIENT_ID)

    systems = await simplisafe.get_systems()
    system = systems[TEST_SYSTEM_ID]

    events = await system.get_events(datetime.now(), 2)

    assert len(events) == 2


async def test_properties(v3_server):
    """Test that base system properties are created properly."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        systems = await simplisafe.get_systems()
        system = systems[TEST_SYSTEM_ID]

        assert system.active is True
        assert not system.alarm_going_off
        assert system.address == TEST_ADDRESS
        assert system.connection_type == "wifi"
        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.state == SystemStates.off
        assert system.system_id == TEST_SYSTEM_ID
        assert system.temperature == 67
        assert system.version == 3


async def test_unknown_sensor_type(caplog, v2_server):
    """Test whether a message is logged upon finding an unknown sensor type."""
    async with aiohttp.ClientSession() as session:
        simplisafe = await get_api(
            TEST_EMAIL, TEST_PASSWORD, session=session, client_id=TEST_CLIENT_ID
        )

        await simplisafe.get_systems()
        assert any("Unknown" in e.message for e in caplog.records)
