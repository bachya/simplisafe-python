"""Define fixtures related to v2 tests."""
import json

import aresponses
import pytest

from ..const import (
    TEST_ACCOUNT_ID, TEST_SUBSCRIPTION_ID, TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO, TEST_USER_ID)


@pytest.fixture()
def v2_server(
        api_token_json, auth_check_json, event_loop, v2_settings_json,
        v2_subscriptions_json):
    """Return a ready-to-query mocked v2 server."""
    server = aresponses.ResponsesMockServer(loop=event_loop)
    server.add(
        'api.simplisafe.com', '/v1/api/token', 'post',
        aresponses.Response(text=json.dumps(api_token_json), status=200))
    server.add(
        'api.simplisafe.com', '/v1/api/authCheck', 'get',
        aresponses.Response(text=json.dumps(auth_check_json), status=200))
    server.add(
        'api.simplisafe.com',
        '/v1/users/{0}/subscriptions'.format(TEST_USER_ID), 'get',
        aresponses.Response(
            text=json.dumps(v2_subscriptions_json), status=200))
    server.add(
        'api.simplisafe.com',
        '/v1/subscriptions/{0}/settings'.format(TEST_SUBSCRIPTION_ID), 'get',
        aresponses.Response(
            text=json.dumps(v2_settings_json), status=200))

    return server


@pytest.fixture()
def v2_settings_json():
    """Return a /v1/subscriptions/<SUBSCRIPTION_ID>/settings response."""
    return {
        "account": TEST_ACCOUNT_ID,
        "type": "all",
        "success": True,
        "settings": {
            "general": {
                "dialingPrefix": "",
                "light": True,
                "doorChime": True,
                "voicePrompts": False,
                "systemVolume": 35,
                "alarmVolume": 100,
                "exitDelay": 120,
                "entryDelayHome": 120,
                "entryDelayAway": 120,
                "alarmDuration": 4
            },
            "pins": {
                "pin1": "1234",
                "pin2": "",
                "pin3": "",
                "pin4": "",
                "pin5": "",
                "duressPin": ""
            },
            "error": {
                "keypadBatteryLow": False,
                "communicationError": False,
                "noDialTone": False,
                "dialError": False,
                "checksumWrong": False,
                "notRegistered": False,
                "messageFailed": False,
                "outOfRange": False
            },
            "sensors": [{
                "type": 1,
                "serial": "195",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Garage Keypad",
                "error": False
            }, {
                "type": 1,
                "serial": "583",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Master Bedroom Keypad",
                "error": False
            }, {
                "type": 2,
                "serial": "654",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Keychain #1",
                "error": False
            }, {
                "type": 2,
                "serial": "429",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Keychain #1",
                "error": False
            }, {
                "type": 3,
                "serial": "425",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 2,
                "sensorData": 0,
                "name": "Front Door Panic",
                "error": False
            }, {
                "type": 3,
                "serial": "874",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 6,
                "sensorData": 0,
                "name": "Master Bathroom Panic",
                "error": False
            }, {
                "type": 3,
                "serial": "427",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 5,
                "sensorData": 0,
                "name": "Master Bedroom Panic",
                "error": False
            }, {
                "type": 4,
                "serial": "672",
                "setting": 2,
                "instant": False,
                "enotify": False,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Main Level Motion",
                "error": False
            }, {
                "type": 4,
                "serial": "119",
                "setting": 2,
                "instant": False,
                "enotify": False,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Basement Motion",
                "error": False
            }, {
                "type": 5,
                "serial": "324",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 2,
                "sensorData": 210,
                "name": "Master Window #1",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "609",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 0,
                "sensorData": 130,
                "name": "Door to Garage",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "936",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 4,
                "sensorData": 178,
                "name": "Basement Window #1",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "102",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 4,
                "sensorData": 162,
                "name": "Family Room Window #1",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "419",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 4,
                "sensorData": 114,
                "name": "Family Room Window #2",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "199",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 2,
                "sensorData": 226,
                "name": "Master Window #2",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "609",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 1,
                "sensorData": 210,
                "name": "Master Bathroom Window",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "84",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 0,
                "sensorData": 82,
                "name": "Front Door",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "190",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 1,
                "sensorData": 210,
                "name": "Back Patio Door",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "939",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 2,
                "sensorData": 162,
                "name": "Office Window #2",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "460",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 3,
                "sensorData": 178,
                "name": "Basement Window #2",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "231",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 2,
                "sensorData": 162,
                "name": "Office Window #1",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "271",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 1,
                "sensorData": 242,
                "name": "Equipment Room Window",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 5,
                "serial": "707",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 6,
                "sensorData": 178,
                "name": "Basement Bedroom Windo",
                "error": False,
                "entryStatus": "closed"
            }, {
                "type": 6,
                "serial": "87",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 3,
                "sensorData": 240,
                "name": "Office Glass Break",
                "error": False,
                "battery": "ok"
            }, {
                "type": 6,
                "serial": "30",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 2,
                "sensorData": 0,
                "name": "Equipment Room Glass",
                "error": False,
                "battery": "ok"
            }, {
                "type": 6,
                "serial": "205",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 3,
                "sensorData": 224,
                "name": "Master Bathroom Glass",
                "error": False,
                "battery": "ok"
            }, {
                "type": 6,
                "serial": "143",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 2,
                "sensorData": 240,
                "name": "Basement Glass Break",
                "error": False,
                "battery": "ok"
            }, {
                "type": 6,
                "serial": "527",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 1,
                "sensorData": 32,
                "name": "Basement Bedroom Glass",
                "error": False,
                "battery": "ok"
            }, {
                "type": 6,
                "serial": "132",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 3,
                "sensorData": 240,
                "name": "Kitchen Glass Break",
                "error": False,
                "battery": "ok"
            }, {
                "type": 6,
                "serial": "199",
                "setting": 1,
                "instant": False,
                "enotify": False,
                "sensorStatus": 2,
                "sensorData": 240,
                "name": "Master Glass Break",
                "error": False,
                "battery": "ok"
            }, {
                "type": 9,
                "serial": "314",
                "setting": 63,
                "instant": True,
                "enotify": True,
                "sensorStatus": 6,
                "sensorData": 0,
                "name": "Washing Machine",
                "error": False
            }, {
                "type": 9,
                "serial": "372",
                "setting": 63,
                "instant": True,
                "enotify": True,
                "sensorStatus": 4,
                "sensorData": 0,
                "name": "Refrigerator Water",
                "error": False
            }, {
                "type": 8,
                "serial": "620",
                "setting": 63,
                "instant": True,
                "enotify": True,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Upstairs Smoke",
                "error": False,
                "battery": "ok"
            }, {
                "type": 8,
                "serial": "994",
                "setting": 63,
                "instant": True,
                "enotify": True,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Downstairs Smoke",
                "error": False,
                "battery": "ok"
            }, {
                "type": 7,
                "serial": "507",
                "setting": 63,
                "instant": True,
                "enotify": True,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Upstairs CO",
                "error": False,
                "battery": "ok"
            }, {
                "type": 42,
                "serial": "974",
                "setting": 63,
                "instant": True,
                "enotify": True,
                "sensorStatus": 0,
                "sensorData": 0,
                "name": "Downstairs CO",
                "error": False,
                "battery": "ok"
            }, {}, {}, {}, {}, {}]
        },
        "lastUpdated": 1521939555,
        "lastStatus": "success_set"
    }


@pytest.fixture()
def v2_state_away_json():
    """
    Return a /v1/subscriptions/<SUBSCRIPTION_ID>/state?state=away response
    with parameters needed to set the system to away.
    """
    return {
        "success": True,
        "reason": None,
        "requestedState": "away",
        "lastUpdated": 1534725096,
        "exitDelay": 120
    }


@pytest.fixture()
def v2_state_home_json():
    """
    Return a /v1/subscriptions/<SUBSCRIPTION_ID>/state?state=home response
    with parameters needed to set the system to home.
    """
    return {
        "success": True,
        "reason": None,
        "requestedState": "home",
        "lastUpdated": 1534725096,
        "exitDelay": 120
    }


@pytest.fixture()
def v2_state_off_json():
    """
    Return a /v1/subscriptions/<SUBSCRIPTION_ID>/state?state=off response
    with parameters needed to set the system to off.
    """
    return {
        "success": True,
        "reason": None,
        "requestedState": "off",
        "lastUpdated": 1534725096,
        "exitDelay": 120
    }


@pytest.fixture()
def v2_subscriptions_json():
    """Return a /v1/users/<USER_ID>/subscriptions response."""
    return {
        "subscriptions": [{
            "uid": TEST_USER_ID,
            "sid": TEST_SYSTEM_ID,
            "sStatus": 20,
            "activated": 1445034752,
            "planName": "24/7 Interactive Alarm Monitoring + Alerts",
            "pinUnlocked": True,
            "location": {
                "sid": TEST_SYSTEM_ID,
                "uid": TEST_USER_ID,
                "account": TEST_ACCOUNT_ID,
                "street1": "1234 Main Street",
                "street2": "",
                "locationName": "",
                "city": "Atlantis",
                "state": "UW",
                "zip": "12345",
                "county": "SEA",
                "notes": "",
                "residenceType": 2,
                "numAdults": 2,
                "numChildren": 0,
                "safeWord": "panic",
                "signature": "John Allen Doe",
                "timeZone": 2,
                "primaryContacts": [{
                    "name": "John Doe",
                    "phone": "1234567890"
                }],
                "secondaryContacts": [{
                    "name": "Jane Doe",
                    "phone": "9876543210"
                }],
                "copsOptIn": False,
                "smashSafeOptIn": False,
                "certificateUri":
                    "https://simplisafe.com/account2/12345/alarm-certificate",
                "locationOffset": -360,
                "nestStructureId": "",
                "system": {
                    "serial": TEST_SYSTEM_SERIAL_NO,
                    "alarmState": "OFF",
                    "alarmStateTimestamp": 0,
                    "isAlarming": False,
                    "version": 2,
                    "temperature": 67,
                    "exitDelayRemaining": 60,
                    "cameras": [],
                    "stateUpdated": 1534625833,
                    "messages": []
                }
            },
            "currency": "USD",
            "country": "US",
            "data": "",
            "billDate": 1537187552,
            "features": {
                "monitoring": True,
                "alerts": True,
                "online": True,
                "hazard": False,
                "video": False
            },
            "creditCard": {
                "type": "Mastercard",
                "lastFour": "1234"
            },
            "pinUnlockedBy":
                "pin"
        }]
    }
