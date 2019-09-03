"""Define general fixtures for tests."""
import pytest

from ..const import (
    TEST_ACCESS_TOKEN,
    TEST_ACCOUNT_ID,
    TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID,
    TEST_USER_ID,
)


@pytest.fixture()
def api_token_json():
    """Return a /v1/api/token response."""
    return {
        "access_token": TEST_ACCESS_TOKEN,
        "refresh_token": TEST_REFRESH_TOKEN,
        "expires_in": 3600,
        "token_type": "Bearer",
    }


@pytest.fixture()
def auth_check_json():
    """Return a /v1/api/authCheck response."""
    return {"userId": TEST_USER_ID, "isAdmin": False}


@pytest.fixture()
def events_json():
    """Return a /v1/subscriptions/<SUBSCRIPTION_ID>/events response."""
    return {
        "numEvents": 2,
        "lastEventTimestamp": 1534035861,
        "events": [
            {
                "eventId": 2921814837,
                "eventTimestamp": 1534720376,
                "eventCid": 3401,
                "zoneCid": "0",
                "sensorType": 1,
                "sensorSerial": "123",
                "account": TEST_ACCOUNT_ID,
                "userId": TEST_USER_ID,
                "sid": TEST_SUBSCRIPTION_ID,
                "info": "System Armed (Away) by Keypad Garage Keypad",
                "pinName": "",
                "sensorName": "Garage Keypad",
                "messageSubject": "SimpliSafe System Armed (away mode)",
                "messageBody": "System Armed (away mode)",
                "eventType": "activity",
                "timezone": 2,
                "locationOffset": -360,
                "videoStartedBy": "",
                "video": {},
            },
            {
                "eventId": 2920433155,
                "eventTimestamp": 1534702778,
                "eventCid": 1400,
                "zoneCid": "1",
                "sensorType": 1,
                "sensorSerial": "456",
                "account": TEST_ACCOUNT_ID,
                "userId": TEST_USER_ID,
                "sid": TEST_SUBSCRIPTION_ID,
                "info": "System Disarmed by Master PIN",
                "pinName": "Master PIN",
                "sensorName": "Garage Keypad",
                "messageSubject": "SimpliSafe System Disarmed",
                "messageBody": "System Disarmed",
                "eventType": "activity",
                "timezone": 2,
                "locationOffset": -360,
                "videoStartedBy": "",
                "video": {},
            },
        ],
    }


@pytest.fixture()
def invalid_credentials_json():
    """Return a response related to invalid credentials."""
    return {
        "error": "invalid_grant",
        "error_description": "Invalid resource owner credentials",
    }


@pytest.fixture()
def latest_event_json():
    """Return a response related the most recent system event."""
    return {
        "numEvents": 50,
        "lastEventTimestamp": 1564018073,
        "events": [
            {
                "eventId": 1234567890,
                "eventTimestamp": 1564018073,
                "eventCid": 1400,
                "zoneCid": "2",
                "sensorType": 1,
                "sensorSerial": "01010101",
                "account": "00011122",
                "userId": TEST_USER_ID,
                "sid": TEST_SUBSCRIPTION_ID,
                "info": "System Disarmed by PIN 2",
                "pinName": "",
                "sensorName": "Kitchen",
                "messageSubject": "SimpliSafe System Disarmed",
                "messageBody": "System Disarmed: Your SimpliSafe security system was "
                "disarmed Keypad PIN 2 at 1234 Main Street on 7-28-19 at 1:30 pm",
                "eventType": "activity",
                "timezone": 2,
                "locationOffset": -360,
                "videoStartedBy": "",
                "video": {},
            }
        ],
    }


@pytest.fixture()
def unavailable_feature_json():
    """Return a response related to any unavailable request."""
    return {
        "errorType": "NoRemoteManagement",
        "code": 403,
        "message": f"Subscription {TEST_SUBSCRIPTION_ID} does not support remote management",
    }
