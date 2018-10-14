"""Define general fixtures for tests."""
import pytest

from ..const import (
    TEST_ACCESS_TOKEN, TEST_ACCOUNT_ID, TEST_REFRESH_TOKEN,
    TEST_SUBSCRIPTION_ID, TEST_USER_ID)


@pytest.fixture()
def api_token_json():
    """Return a /v1/api/token response."""
    return {
        "access_token": TEST_ACCESS_TOKEN,
        "refresh_token": TEST_REFRESH_TOKEN,
        "expires_in": 3600,
        "token_type": "Bearer"
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
        "events": [{
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
            "video": {}
        }, {
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
            "video": {}
        }]
    }


@pytest.fixture()
def invalid_credentials_json():
    """Return a response related to invalid credentials."""
    return {
        "error": "invalid_grant",
        "error_description": "Invalid resource owner credentials"
    }


@pytest.fixture()
def unavailable_feature_json():
    """Return a response related to any unavailable request."""
    return {
        "errorType": "NoRemoteManagement",
        "code": 403,
        "message":
            "Subscription {0} does not support remote management".format(
                TEST_SUBSCRIPTION_ID)
    }
