"""Define tests for v3 System objects."""
# pylint: disable=too-many-lines
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, cast
from unittest.mock import Mock

import aiohttp
import pytest
from aresponses import ResponsesMockServer

from simplipy import API
from simplipy.errors import (
    EndpointUnavailableError,
    InvalidCredentialsError,
    MaxUserPinsExceededError,
    PinError,
    RequestError,
    SimplipyError,
)
from simplipy.system import SystemStates
from simplipy.system.v3 import SystemV3, Volume
from tests.common import (
    TEST_AUTHORIZATION_CODE,
    TEST_CODE_VERIFIER,
    TEST_SUBSCRIPTION_ID,
    TEST_SYSTEM_ID,
    TEST_SYSTEM_SERIAL_NO,
    TEST_USER_ID,
)


@pytest.mark.asyncio
async def test_as_dict(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test dumping the system as a dict."""
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert system.as_dict() == {
            "address": "1234 Main Street",
            "alarm_going_off": False,
            "connection_type": "wifi",
            "notifications": [
                {
                    "notification_id": "xxxxxxxxxxxxxxxxxxxxxxxx",
                    "text": "Power Outage - Backup battery in use.",
                    "category": "error",
                    "code": "2000",
                    "timestamp": 1581823228,
                    "received_dt": datetime(2020, 2, 16, 3, 20, 28, tzinfo=timezone.utc),
                    "link": "http://link.to.info",
                    "link_label": "More Info",
                }
            ],
            "serial": "1234ABCD",
            "state": 10,
            "system_id": 12345,
            "temperature": 67,
            "version": 3,
            "sensors": [
                {
                    "name": "Fire Door",
                    "serial": "825",
                    "type": 5,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Front Door",
                    "serial": "14",
                    "type": 5,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Patio Door",
                    "serial": "185",
                    "type": 5,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": True,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": True,
                    "triggered": False,
                },
                {
                    "name": "Basement",
                    "serial": "236",
                    "type": 13,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "alarmVolume": 3,
                        "doorChime": 0,
                        "exitBeeps": 0,
                        "entryBeeps": 2,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Front Door",
                    "serial": "789",
                    "type": 3,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {"alarm": 1},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Master BR",
                    "serial": "822",
                    "type": 3,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {"alarm": 1},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Kitchen",
                    "serial": "972",
                    "type": 1,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {"lowPowerMode": False, "alarm": 1},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Upstairs",
                    "serial": "93",
                    "type": 8,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Downstairs",
                    "serial": "650",
                    "type": 8,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Basement N",
                    "serial": "491",
                    "type": 6,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Mud Counter",
                    "serial": "280",
                    "type": 6,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Basement S",
                    "serial": "430",
                    "type": 6,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Laundry",
                    "serial": "129",
                    "type": 9,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {"alarm": 1},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Basement",
                    "serial": "975",
                    "type": 9,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {"alarm": 1},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Fridge",
                    "serial": "382",
                    "type": 9,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {"alarm": 1},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Basement",
                    "serial": "320",
                    "type": 10,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {"highTemp": 95, "lowTemp": 41, "alarm": 1},
                    "trigger_instantly": False,
                    "triggered": False,
                    "temperature": 67,
                },
                {
                    "name": "Upstairs",
                    "serial": "785",
                    "type": 4,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 0,
                        "home": 0,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Downstairs",
                    "serial": "934",
                    "type": 4,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 0,
                        "home": 0,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Landing",
                    "serial": "634",
                    "type": 6,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Living Room",
                    "serial": "801",
                    "type": 6,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Eating Area",
                    "serial": "946",
                    "type": 6,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "instantTrigger": False,
                        "away2": 1,
                        "away": 1,
                        "home2": 1,
                        "home": 1,
                        "off": 0,
                    },
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Front Door",
                    "serial": "987a",
                    "type": 253,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Front Door",
                    "serial": "654a",
                    "type": 253,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Front Door",
                    "serial": "321a",
                    "type": 253,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {},
                    "trigger_instantly": False,
                    "triggered": False,
                },
                {
                    "name": "Kitchen",
                    "serial": "00000000",
                    "type": 14,
                    "error": False,
                    "low_battery": False,
                    "offline": True,
                    "settings": {},
                    "trigger_instantly": False,
                    "triggered": False,
                },
            ],
            "alarm_duration": 240,
            "alarm_volume": 3,
            "battery_backup_power_level": 5293,
            "cameras": [
                {
                    "camera_settings": {
                        "cameraName": "Camera",
                        "pictureQuality": "720p",
                        "nightVision": "auto",
                        "statusLight": "off",
                        "micSensitivity": 100,
                        "micEnable": True,
                        "speakerVolume": 75,
                        "motionSensitivity": 0,
                        "shutterHome": "closedAlarmOnly",
                        "shutterAway": "open",
                        "shutterOff": "closedAlarmOnly",
                        "wifiSsid": "",
                        "canStream": False,
                        "canRecord": False,
                        "pirEnable": True,
                        "vaEnable": True,
                        "notificationsEnable": False,
                        "enableDoorbellNotification": True,
                        "doorbellChimeVolume": "off",
                        "privacyEnable": False,
                        "hdr": False,
                        "vaZoningEnable": False,
                        "vaZoningRows": 0,
                        "vaZoningCols": 0,
                        "vaZoningMask": [],
                        "maxDigitalZoom": 10,
                        "supportedResolutions": ["480p", "720p"],
                        "admin": {
                            "IRLED": 0,
                            "pirSens": 0,
                            "statusLEDState": 1,
                            "lux": "lowLux",
                            "motionDetectionEnabled": False,
                            "motionThresholdZero": 0,
                            "motionThresholdOne": 10000,
                            "levelChangeDelayZero": 30,
                            "levelChangeDelayOne": 10,
                            "audioDetectionEnabled": False,
                            "audioChannelNum": 2,
                            "audioSampleRate": 16000,
                            "audioChunkBytes": 2048,
                            "audioSampleFormat": 3,
                            "audioSensitivity": 50,
                            "audioThreshold": 50,
                            "audioDirection": 0,
                            "bitRate": 284,
                            "longPress": 2000,
                            "kframe": 1,
                            "gopLength": 40,
                            "idr": 1,
                            "fps": 20,
                            "firmwareVersion": "2.6.1.107",
                            "netConfigVersion": "",
                            "camAgentVersion": "",
                            "lastLogin": 1600639997,
                            "lastLogout": 1600639944,
                            "pirSampleRateMs": 800,
                            "pirHysteresisHigh": 2,
                            "pirHysteresisLow": 10,
                            "pirFilterCoefficient": 1,
                            "logEnabled": True,
                            "logLevel": 3,
                            "logQDepth": 20,
                            "firmwareGroup": "public",
                            "irOpenThreshold": 445,
                            "irCloseThreshold": 840,
                            "irOpenDelay": 3,
                            "irCloseDelay": 3,
                            "irThreshold1x": 388,
                            "irThreshold2x": 335,
                            "irThreshold3x": 260,
                            "rssi": [[1600935204, -43]],
                            "battery": [],
                            "dbm": 0,
                            "vmUse": 161592,
                            "resSet": 10540,
                            "uptime": 810043.74,
                            "wifiDisconnects": 1,
                            "wifiDriverReloads": 1,
                            "statsPeriod": 3600000,
                            "sarlaccDebugLogTypes": 0,
                            "odProcessingFps": 8,
                            "odObjectMinWidthPercent": 6,
                            "odObjectMinHeightPercent": 24,
                            "odEnableObjectDetection": True,
                            "odClassificationMask": 2,
                            "odClassificationConfidenceThreshold": 0.95,
                            "odEnableOverlay": False,
                            "odAnalyticsLib": 2,
                            "odSensitivity": 85,
                            "odEventObjectMask": 2,
                            "odLuxThreshold": 445,
                            "odLuxHysteresisHigh": 4,
                            "odLuxHysteresisLow": 4,
                            "odLuxSamplingFrequency": 30,
                            "odFGExtractorMode": 2,
                            "odVideoScaleFactor": 1,
                            "odSceneType": 1,
                            "odCameraView": 3,
                            "odCameraFOV": 2,
                            "odBackgroundLearnStationary": True,
                            "odBackgroundLearnStationarySpeed": 15,
                            "odClassifierQualityProfile": 1,
                            "odEnableVideoAnalyticsWhileStreaming": False,
                            "wlanMac": "XX:XX:XX:XX:XX:XX",
                            "region": "us-east-1",
                            "enableWifiAnalyticsLib": False,
                            "ivLicense": "",
                        },
                        "pirLevel": "medium",
                        "odLevel": "medium",
                    },
                    "camera_type": 0,
                    "name": "Camera",
                    "serial": "1234567890",
                    "shutter_open_when_away": True,
                    "shutter_open_when_home": False,
                    "shutter_open_when_off": False,
                    "status": "online",
                    "subscription_enabled": True,
                },
                {
                    "camera_settings": {
                        "cameraName": "Doorbell",
                        "pictureQuality": "720p",
                        "nightVision": "auto",
                        "statusLight": "off",
                        "micSensitivity": 100,
                        "micEnable": True,
                        "speakerVolume": 75,
                        "motionSensitivity": 0,
                        "shutterHome": "closedAlarmOnly",
                        "shutterAway": "open",
                        "shutterOff": "closedAlarmOnly",
                        "wifiSsid": "",
                        "canStream": False,
                        "canRecord": False,
                        "pirEnable": True,
                        "vaEnable": True,
                        "notificationsEnable": False,
                        "enableDoorbellNotification": True,
                        "doorbellChimeVolume": "off",
                        "privacyEnable": False,
                        "hdr": False,
                        "vaZoningEnable": False,
                        "vaZoningRows": 0,
                        "vaZoningCols": 0,
                        "vaZoningMask": [],
                        "maxDigitalZoom": 10,
                        "supportedResolutions": ["480p", "720p"],
                        "admin": {
                            "IRLED": 0,
                            "pirSens": 0,
                            "statusLEDState": 1,
                            "lux": "lowLux",
                            "motionDetectionEnabled": False,
                            "motionThresholdZero": 0,
                            "motionThresholdOne": 10000,
                            "levelChangeDelayZero": 30,
                            "levelChangeDelayOne": 10,
                            "audioDetectionEnabled": False,
                            "audioChannelNum": 2,
                            "audioSampleRate": 16000,
                            "audioChunkBytes": 2048,
                            "audioSampleFormat": 3,
                            "audioSensitivity": 50,
                            "audioThreshold": 50,
                            "audioDirection": 0,
                            "bitRate": 284,
                            "longPress": 2000,
                            "kframe": 1,
                            "gopLength": 40,
                            "idr": 1,
                            "fps": 20,
                            "firmwareVersion": "2.6.1.107",
                            "netConfigVersion": "",
                            "camAgentVersion": "",
                            "lastLogin": 1600639997,
                            "lastLogout": 1600639944,
                            "pirSampleRateMs": 800,
                            "pirHysteresisHigh": 2,
                            "pirHysteresisLow": 10,
                            "pirFilterCoefficient": 1,
                            "logEnabled": True,
                            "logLevel": 3,
                            "logQDepth": 20,
                            "firmwareGroup": "public",
                            "irOpenThreshold": 445,
                            "irCloseThreshold": 840,
                            "irOpenDelay": 3,
                            "irCloseDelay": 3,
                            "irThreshold1x": 388,
                            "irThreshold2x": 335,
                            "irThreshold3x": 260,
                            "rssi": [[1600935204, -43]],
                            "battery": [],
                            "dbm": 0,
                            "vmUse": 161592,
                            "resSet": 10540,
                            "uptime": 810043.74,
                            "wifiDisconnects": 1,
                            "wifiDriverReloads": 1,
                            "statsPeriod": 3600000,
                            "sarlaccDebugLogTypes": 0,
                            "odProcessingFps": 8,
                            "odObjectMinWidthPercent": 6,
                            "odObjectMinHeightPercent": 24,
                            "odEnableObjectDetection": True,
                            "odClassificationMask": 2,
                            "odClassificationConfidenceThreshold": 0.95,
                            "odEnableOverlay": False,
                            "odAnalyticsLib": 2,
                            "odSensitivity": 85,
                            "odEventObjectMask": 2,
                            "odLuxThreshold": 445,
                            "odLuxHysteresisHigh": 4,
                            "odLuxHysteresisLow": 4,
                            "odLuxSamplingFrequency": 30,
                            "odFGExtractorMode": 2,
                            "odVideoScaleFactor": 1,
                            "odSceneType": 1,
                            "odCameraView": 3,
                            "odCameraFOV": 2,
                            "odBackgroundLearnStationary": True,
                            "odBackgroundLearnStationarySpeed": 15,
                            "odClassifierQualityProfile": 1,
                            "odEnableVideoAnalyticsWhileStreaming": False,
                            "wlanMac": "XX:XX:XX:XX:XX:XX",
                            "region": "us-east-1",
                            "enableWifiAnalyticsLib": False,
                            "ivLicense": "",
                        },
                        "pirLevel": "medium",
                        "odLevel": "medium",
                    },
                    "camera_type": 1,
                    "name": "Doorbell",
                    "serial": "1234567892",
                    "shutter_open_when_away": True,
                    "shutter_open_when_home": False,
                    "shutter_open_when_off": False,
                    "status": "online",
                    "subscription_enabled": True,
                },
                {
                    "camera_settings": {
                        "cameraName": "Unknown Camera",
                        "pictureQuality": "720p",
                        "nightVision": "auto",
                        "statusLight": "off",
                        "micSensitivity": 100,
                        "micEnable": True,
                        "speakerVolume": 75,
                        "motionSensitivity": 0,
                        "shutterHome": "closedAlarmOnly",
                        "shutterAway": "open",
                        "shutterOff": "closedAlarmOnly",
                        "wifiSsid": "",
                        "canStream": False,
                        "canRecord": False,
                        "pirEnable": True,
                        "vaEnable": True,
                        "notificationsEnable": False,
                        "enableDoorbellNotification": True,
                        "doorbellChimeVolume": "off",
                        "privacyEnable": False,
                        "hdr": False,
                        "vaZoningEnable": False,
                        "vaZoningRows": 0,
                        "vaZoningCols": 0,
                        "vaZoningMask": [],
                        "maxDigitalZoom": 10,
                        "supportedResolutions": ["480p", "720p"],
                        "admin": {
                            "IRLED": 0,
                            "pirSens": 0,
                            "statusLEDState": 1,
                            "lux": "lowLux",
                            "motionDetectionEnabled": False,
                            "motionThresholdZero": 0,
                            "motionThresholdOne": 10000,
                            "levelChangeDelayZero": 30,
                            "levelChangeDelayOne": 10,
                            "audioDetectionEnabled": False,
                            "audioChannelNum": 2,
                            "audioSampleRate": 16000,
                            "audioChunkBytes": 2048,
                            "audioSampleFormat": 3,
                            "audioSensitivity": 50,
                            "audioThreshold": 50,
                            "audioDirection": 0,
                            "bitRate": 284,
                            "longPress": 2000,
                            "kframe": 1,
                            "gopLength": 40,
                            "idr": 1,
                            "fps": 20,
                            "firmwareVersion": "2.6.1.107",
                            "netConfigVersion": "",
                            "camAgentVersion": "",
                            "lastLogin": 1600639997,
                            "lastLogout": 1600639944,
                            "pirSampleRateMs": 800,
                            "pirHysteresisHigh": 2,
                            "pirHysteresisLow": 10,
                            "pirFilterCoefficient": 1,
                            "logEnabled": True,
                            "logLevel": 3,
                            "logQDepth": 20,
                            "firmwareGroup": "public",
                            "irOpenThreshold": 445,
                            "irCloseThreshold": 840,
                            "irOpenDelay": 3,
                            "irCloseDelay": 3,
                            "irThreshold1x": 388,
                            "irThreshold2x": 335,
                            "irThreshold3x": 260,
                            "rssi": [[1600935204, -43]],
                            "battery": [],
                            "dbm": 0,
                            "vmUse": 161592,
                            "resSet": 10540,
                            "uptime": 810043.74,
                            "wifiDisconnects": 1,
                            "wifiDriverReloads": 1,
                            "statsPeriod": 3600000,
                            "sarlaccDebugLogTypes": 0,
                            "odProcessingFps": 8,
                            "odObjectMinWidthPercent": 6,
                            "odObjectMinHeightPercent": 24,
                            "odEnableObjectDetection": True,
                            "odClassificationMask": 2,
                            "odClassificationConfidenceThreshold": 0.95,
                            "odEnableOverlay": False,
                            "odAnalyticsLib": 2,
                            "odSensitivity": 85,
                            "odEventObjectMask": 2,
                            "odLuxThreshold": 445,
                            "odLuxHysteresisHigh": 4,
                            "odLuxHysteresisLow": 4,
                            "odLuxSamplingFrequency": 30,
                            "odFGExtractorMode": 2,
                            "odVideoScaleFactor": 1,
                            "odSceneType": 1,
                            "odCameraView": 3,
                            "odCameraFOV": 2,
                            "odBackgroundLearnStationary": True,
                            "odBackgroundLearnStationarySpeed": 15,
                            "odClassifierQualityProfile": 1,
                            "odEnableVideoAnalyticsWhileStreaming": False,
                            "wlanMac": "XX:XX:XX:XX:XX:XX",
                            "region": "us-east-1",
                            "enableWifiAnalyticsLib": False,
                            "ivLicense": "",
                        },
                        "pirLevel": "medium",
                        "odLevel": "medium",
                    },
                    "camera_type": 99,
                    "name": "Unknown Camera",
                    "serial": "1234567891",
                    "shutter_open_when_away": True,
                    "shutter_open_when_home": False,
                    "shutter_open_when_off": False,
                    "status": "online",
                    "subscription_enabled": True,
                },
            ],
            "chime_volume": 2,
            "entry_delay_away": 30,
            "entry_delay_home": 30,
            "exit_delay_away": 60,
            "exit_delay_home": 0,
            "gsm_strength": -73,
            "light": True,
            "locks": [
                {
                    "name": "Front Door",
                    "serial": "987",
                    "type": 16,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "autoLock": 3,
                        "away": 1,
                        "home": 1,
                        "awayToOff": 0,
                        "homeToOff": 1,
                    },
                    "disabled": False,
                    "lock_low_battery": False,
                    "pin_pad_low_battery": False,
                    "pin_pad_offline": False,
                    "state": 1,
                },
                {
                    "name": "Back Door",
                    "serial": "654",
                    "type": 16,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "autoLock": 3,
                        "away": 1,
                        "home": 1,
                        "awayToOff": 0,
                        "homeToOff": 1,
                    },
                    "disabled": False,
                    "lock_low_battery": False,
                    "pin_pad_low_battery": False,
                    "pin_pad_offline": False,
                    "state": 2,
                },
                {
                    "name": "Side Door",
                    "serial": "321",
                    "type": 16,
                    "error": False,
                    "low_battery": False,
                    "offline": False,
                    "settings": {
                        "autoLock": 3,
                        "away": 1,
                        "home": 1,
                        "awayToOff": 0,
                        "homeToOff": 1,
                    },
                    "disabled": False,
                    "lock_low_battery": False,
                    "pin_pad_low_battery": False,
                    "pin_pad_offline": False,
                    "state": 99,
                },
            ],
            "offline": False,
            "power_outage": False,
            "rf_jamming": False,
            "voice_prompt_volume": 2,
            "wall_power_level": 5933,
            "wifi_ssid": "MY_WIFI",
            "wifi_strength": -49,
        }

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_alarm_state(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that we can get the alarm state."""
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert system.state == SystemStates.OFF

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_clear_notifications(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test clearing all active notifications."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/messages",
            "delete",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]
            await system.async_clear_notifications()
            assert system.notifications == []

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_get_last_event(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    latest_event_response: dict[str, Any],
) -> None:
    """Test getting the latest event."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
            "get",
            response=aiohttp.web_response.json_response(
                latest_event_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]
            latest_event = await system.async_get_latest_event()
            assert latest_event["eventId"] == 1234567890

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_get_pins(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test getting PINs associated with a V3 system."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]
            pins = await system.async_get_pins()
            assert len(pins) == 4
            assert pins["master"] == "1234"
            assert pins["duress"] == "9876"
            assert pins["Test 1"] == "3454"
            assert pins["Test 2"] == "5424"

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_async_get_systems(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test the ability to get systems attached to a v3 account."""
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        assert len(systems) == 1

        system = systems[TEST_SYSTEM_ID]
        assert system.serial == TEST_SYSTEM_SERIAL_NO
        assert system.system_id == TEST_SYSTEM_ID
        assert len(system.sensors) == 25

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_empty_events(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    events_response: dict[str, Any],
) -> None:
    """Test that an empty events structure is handled correctly."""
    events_response["events"] = []

    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
            "get",
            response=aiohttp.web_response.json_response(events_response, status=200),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            # Test the events key existing, but being empty:
            with pytest.raises(SimplipyError):
                _ = await system.async_get_latest_event()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_lock_state_update_bug(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    caplog: Mock,
    v3_state_response: dict[str, Any],
) -> None:
    """Test halting updates within a 15-second window from arming/disarming."""
    caplog.set_level(logging.INFO)

    v3_state_response["state"] = "AWAY"

    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
            "post",
            response=aiohttp.web_response.json_response(v3_state_response, status=200),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.async_set_away()
            assert system.state == SystemStates.AWAY

            await system.async_update()
            assert any("Skipping system update" in e.message for e in caplog.records)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_missing_events(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    events_response: dict[str, Any],
) -> None:
    """Test that an altogether-missing events structure is handled correctly."""
    events_response.pop("events")

    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/subscriptions/{TEST_SUBSCRIPTION_ID}/events",
            "get",
            response=aiohttp.web_response.json_response(events_response, status=200),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            # Test that the events key exists, but is empty:
            with pytest.raises(SimplipyError):
                _ = await system.async_get_latest_event()

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_no_state_change_on_failure(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that the system doesn't change state on an error."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
            "post",
            response=aresponses.Response(text="Unauthorized", status=401),
        )
        authenticated_simplisafe_server_v3.add(
            "auth.simplisafe.com",
            "/oauth/token",
            "post",
            response=aresponses.Response(text="Unauthorized", status=401),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )

            # pylint: disable=protected-access
            # Manually set the expiration datetime to force a refresh token flow:
            simplisafe._token_last_refreshed = datetime.utcnow() - timedelta(seconds=30)

            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]
            assert system.state == SystemStates.OFF

            with pytest.raises(InvalidCredentialsError):
                await system.async_set_away()
            assert system.state == SystemStates.OFF

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_properties(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test that v3 system properties are available."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])
            assert system.alarm_duration == 240
            assert system.alarm_volume == Volume.HIGH
            assert system.battery_backup_power_level == 5293
            assert system.chime_volume == Volume.MEDIUM
            assert system.connection_type == "wifi"
            assert system.entry_delay_away == 30
            assert system.entry_delay_home == 30
            assert system.exit_delay_away == 60
            assert system.exit_delay_home == 0
            assert system.gsm_strength == -73
            assert system.light is True
            assert system.offline is False
            assert system.power_outage is False
            assert system.rf_jamming is False
            assert system.voice_prompt_volume == Volume.MEDIUM
            assert system.wall_power_level == 5933
            assert system.wifi_ssid == "MY_WIFI"
            assert system.wifi_strength == -49

            # Test "setting" various system properties by overriding their values, then
            # calling the update functions:
            system.settings_data["settings"]["normal"]["alarmDuration"] = 0
            system.settings_data["settings"]["normal"]["alarmVolume"] = 0
            system.settings_data["settings"]["normal"]["doorChime"] = 0
            system.settings_data["settings"]["normal"]["entryDelayAway"] = 0
            system.settings_data["settings"]["normal"]["entryDelayHome"] = 0
            system.settings_data["settings"]["normal"]["exitDelayAway"] = 0
            system.settings_data["settings"]["normal"]["exitDelayHome"] = 1000
            system.settings_data["settings"]["normal"]["light"] = False
            system.settings_data["settings"]["normal"]["voicePrompts"] = 0

            await system.async_set_properties(
                {
                    "alarm_duration": 240,
                    "alarm_volume": Volume.HIGH,
                    "chime_volume": Volume.MEDIUM,
                    "entry_delay_away": 30,
                    "entry_delay_home": 30,
                    "exit_delay_away": 60,
                    "exit_delay_home": 0,
                    "light": True,
                    "voice_prompt_volume": Volume.MEDIUM,
                }
            )
            assert system.alarm_duration == 240
            assert system.alarm_volume == Volume.HIGH
            assert system.chime_volume == Volume.MEDIUM
            assert system.entry_delay_away == 30
            assert system.entry_delay_home == 30
            assert system.exit_delay_away == 60
            assert system.exit_delay_home == 0
            assert system.light is True
            assert system.voice_prompt_volume == Volume.MEDIUM

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_remove_nonexistent_pin(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test throwing an error when removing a nonexistent PIN."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            with pytest.raises(PinError) as err:
                await system.async_remove_pin("0000")
                assert "Refusing to delete nonexistent PIN" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_remove_pin(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test removing a PIN in a V3 system."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        v3_settings_response["settings"]["pins"]["users"][1]["pin"] = ""
        v3_settings_response["settings"]["pins"]["users"][1]["name"] = ""

        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]
            latest_pins = await system.async_get_pins()
            assert len(latest_pins) == 4

            await system.async_remove_pin("Test 2")
            latest_pins = await system.async_get_pins()
            assert len(latest_pins) == 3

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_remove_reserved_pin(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test throwing an error when removing a reserved PIN."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            with pytest.raises(PinError) as err:
                await system.async_remove_pin("master")
                assert "Refusing to delete reserved PIN" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_duplicate_pin(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test throwing an error when setting a duplicate PIN."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            with pytest.raises(PinError) as err:
                simplisafe = await API.async_from_auth(
                    TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
                )
                systems = await simplisafe.async_get_systems()
                system = systems[TEST_SYSTEM_ID]
                await system.async_set_pin("whatever", "3454")
                assert "Refusing to create duplicate PIN" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_invalid_property(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test that setting an invalid property raises a ValueError."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "post",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system: SystemV3 = cast(SystemV3, systems[TEST_SYSTEM_ID])

            with pytest.raises(ValueError):
                await system.async_set_properties({"foo": 1})

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_max_user_pins(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test throwing an error when setting too many user PINs."""
    v3_settings_response["settings"]["pins"]["users"] = [
        {
            "_id": "1271279d966212121124c6",
            "pin": "1234",
            "name": "Test 1",
        },
        {
            "_id": "1271279d966212121124c7",
            "pin": "5678",
            "name": "Test 2",
        },
        {
            "_id": "1271279d966212121124c8",
            "pin": "9012",
            "name": "Test 3",
        },
        {
            "_id": "1271279d966212121124c9",
            "pin": "3456",
            "name": "Test 4",
        },
    ]

    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            with pytest.raises(MaxUserPinsExceededError) as err:
                simplisafe = await API.async_from_auth(
                    TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
                )
                systems = await simplisafe.async_get_systems()
                system = systems[TEST_SYSTEM_ID]
                await system.async_set_pin("whatever", "8121")
                assert "Refusing to create more than" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_pin(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_settings_response: dict[str, Any],
) -> None:
    """Test setting a PIN in a V3 system."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        v3_settings_response["settings"]["pins"]["users"][2]["pin"] = "1274"
        v3_settings_response["settings"]["pins"]["users"][2]["name"] = "whatever"

        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/pins",
            "post",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            latest_pins = await system.async_get_pins()
            assert len(latest_pins) == 4

            await system.async_set_pin("whatever", "1274")
            latest_pins = await system.async_get_pins()
            assert len(latest_pins) == 5

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pin",
    ["1234", "5678", "7890", "6543", "4321"],
)
async def test_set_pin_sequence(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    pin: str,
) -> None:
    """Test throwing an error when setting a PIN that is in a sequence."""
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.async_set_pin("label", pin)
            assert "Refusing to create PIN that is a sequence" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_pin_wrong_chars(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test throwing an error when setting a PIN with non-digits."""
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.async_set_pin("whatever", "abcd")
            assert "PINs can only contain numbers" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_pin_wrong_length(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test throwing an error when setting a PIN with the wrong length."""
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        with pytest.raises(PinError) as err:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.async_set_pin("whatever", "1122334455")
            assert "digits long" in str(err)

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_set_states(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    v3_state_response: dict[str, Any],
) -> None:
    """Test the ability to set the state of the system."""
    v3_state_response["state"] = "AWAY"

    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/away",
            "post",
            response=aiohttp.web_response.json_response(v3_state_response, status=200),
        )

        v3_state_response["state"] = "HOME"

        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/home",
            "post",
            response=aiohttp.web_response.json_response(v3_state_response, status=200),
        )

        v3_state_response["state"] = "OFF"

        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/state/off",
            "post",
            response=aiohttp.web_response.json_response(v3_state_response, status=200),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.async_set_away()
            state = system.state
            assert state == SystemStates.AWAY
            await system.async_set_home()
            state = system.state
            assert state == SystemStates.HOME
            await system.async_set_off()
            state = system.state
            assert state == SystemStates.OFF

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_system_notifications(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test getting system notifications."""
    async with authenticated_simplisafe_server_v3, aiohttp.ClientSession() as session:
        simplisafe = await API.async_from_auth(
            TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
        )
        systems = await simplisafe.async_get_systems()
        system = systems[TEST_SYSTEM_ID]
        assert len(system.notifications) == 1

        notification1 = system.notifications[0]
        assert notification1.notification_id == "xxxxxxxxxxxxxxxxxxxxxxxx"
        assert notification1.text == "Power Outage - Backup battery in use."
        assert notification1.category == "error"
        assert notification1.code == "2000"
        assert notification1.received_dt == datetime(
            2020, 2, 16, 3, 20, 28, tzinfo=timezone.utc
        )
        assert notification1.link == "http://link.to.info"
        assert notification1.link_label == "More Info"

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_unavailable_endpoint(
    aresponses: ResponsesMockServer,
    unavailable_endpoint_response: dict[str, Any],
    authenticated_simplisafe_server_v3: ResponsesMockServer,
) -> None:
    """Test that an unavailable endpoint logs a message."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                unavailable_endpoint_response, status=403
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            with pytest.raises(EndpointUnavailableError):
                await system.async_update(
                    include_subscription=False, include_devices=False
                )

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_update_system_data(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    subscriptions_response: dict[str, Any],
    v3_sensors_response: dict[str, Any],
    v3_settings_response: dict[str, Any],
) -> None:
    """Test getting updated data for a v3 system."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            response=aiohttp.web_response.json_response(
                subscriptions_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            response=aiohttp.web_response.json_response(
                v3_sensors_response, status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE, TEST_CODE_VERIFIER, session=session
            )
            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            await system.async_update()

            assert system.serial == TEST_SYSTEM_SERIAL_NO
            assert system.system_id == TEST_SYSTEM_ID
            assert len(system.sensors) == 25

    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_update_error(
    aresponses: ResponsesMockServer,
    authenticated_simplisafe_server_v3: ResponsesMockServer,
    subscriptions_response: dict[str, Any],
    v3_settings_response: dict[str, Any],
) -> None:
    """Test handling a generic error during update."""
    async with authenticated_simplisafe_server_v3:
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/users/{TEST_USER_ID}/subscriptions",
            "get",
            response=aiohttp.web_response.json_response(
                subscriptions_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/settings/normal",
            "get",
            response=aiohttp.web_response.json_response(
                v3_settings_response, status=200
            ),
        )
        authenticated_simplisafe_server_v3.add(
            "api.simplisafe.com",
            f"/v1/ss3/subscriptions/{TEST_SUBSCRIPTION_ID}/sensors",
            "get",
            response=aresponses.Response(text="Server Error", status=500),
        )

        async with aiohttp.ClientSession() as session:
            simplisafe = await API.async_from_auth(
                TEST_AUTHORIZATION_CODE,
                TEST_CODE_VERIFIER,
                session=session,
                # Set so that our tests don't take too long:
                request_retries=1,
            )

            systems = await simplisafe.async_get_systems()
            system = systems[TEST_SYSTEM_ID]

            with pytest.raises(RequestError):
                await system.async_update()

    aresponses.assert_plan_strictly_followed()
