"""Define constants for use in tests."""
TEST_ACCESS_TOKEN = "abcde12345"
TEST_ACCOUNT_ID = 12345
TEST_ADDRESS = "1234 Main Street"
TEST_EMAIL = "user@email.com"
TEST_LOCK_ID = "987"
TEST_LOCK_ID_2 = "654"
TEST_LOCK_ID_3 = "321"
TEST_PASSWORD = "12345"
TEST_REFRESH_TOKEN = "qrstu98765"
TEST_SUBSCRIPTION_ID = 12345
TEST_SYSTEM_ID = 12345
TEST_SYSTEM_SERIAL_NO = "1234ABCD"
TEST_USER_ID = 12345

RESPONSE_WEBSOCKET_KNOWN_EVENT = {
    "eventId": "xxxxxxxxxxxxx",
    "eventTimestamp": "xxxxxxxxxxxxx",
    "eventCid": 1400,
    "zoneCid": "1",
    "sensorType": 1,
    "sensorSerial": "xxxxx",
    "account": "xxxxx",
    "userId": "xxxxxxx",
    "sid": "xxxxxxx",
    "info": "System Disarmed by Master PIN",
    "pinName": "Master PIN",
    "sensorName": "Garage Keypad",
    "messageSubject": "SimpliSafe System Disarmed",
    "messageBody": "System Disarmed: Your SimpliSafe security system was disarmed.",
    "eventType": "activity",
    "timezone": 2,
    "locationOffset": -420,
    "videoStartedBy": "",
    "video": {},
}

RESPONSE_WEBSOCKET_UNKNOWN_EVENT = {
    "eventId": 1231231231,
    "eventTimestamp": 1231231231,
    "eventCid": 1231,
    "zoneCid": "3",
    "sensorType": 0,
    "sensorSerial": "",
    "account": "xxxxxxxx",
    "userId": 123123,
    "sid": 123123,
    "info": "System Went Totally Nuts!",
    "pinName": "",
    "sensorName": "",
    "messageSubject": "SimpliSafe System Armed (home mode)",
    "messageBody": "System Armed (home mode)",
    "eventType": "activity",
    "timezone": 2,
    "locationOffset": -420,
    "videoStartedBy": "",
    "video": {},
}
