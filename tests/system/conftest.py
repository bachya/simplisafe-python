"""Define fixtures for system-related tests."""
import json

import pytest

from tests.common import load_fixture


@pytest.fixture()
def subscriptions_alarm_state_response(subscriptions_fixture_filename):
    """Define a fixture for a subscription with an ALARM alarm state."""
    raw = load_fixture(subscriptions_fixture_filename)
    data = json.loads(raw)
    data["subscriptions"][0]["location"]["system"]["alarmState"] = "ALARM"
    return json.dumps(data)


@pytest.fixture()
def settings_missing_basestation_response(v3_settings_response):
    """Define a fixture for settings that are missing base station status."""
    data = json.loads(v3_settings_response)
    data["settings"].pop("basestationStatus")
    return json.dumps(data)


@pytest.fixture()
def subscriptions_missing_notifications_response(subscriptions_fixture_filename):
    """Define a fixture for a subscription that is missing notifications."""
    raw = load_fixture(subscriptions_fixture_filename)
    data = json.loads(raw)
    data["subscriptions"][0]["location"]["system"].pop("messages")
    return json.dumps(data)


@pytest.fixture()
def subscriptions_unknown_state_response(subscriptions_fixture_filename):
    """Define a fixture for a subscription with an unknown alarm state."""
    raw = load_fixture(subscriptions_fixture_filename)
    data = json.loads(raw)
    data["subscriptions"][0]["location"]["system"]["alarmState"] = "NOT_REAL_STATE"
    return json.dumps(data)
