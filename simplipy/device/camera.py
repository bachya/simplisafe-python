"""Define SimpliSafe cameras (SimpliCams)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, cast
from urllib.parse import urlencode

from simplipy.const import LOGGER
from simplipy.device import DeviceV3

if TYPE_CHECKING:
    from simplipy.system.v3 import SystemV3

MEDIA_URL_BASE = "https://media.simplisafe.com/v1"
DEFAULT_VIDEO_WIDTH = 1280
DEFAULT_AUDIO_ENCODING = "AAC"

CAMERA_MODEL_CAMERA = "camera"
CAMERA_MODEL_DOORBELL = "doorbell"
CAMERA_MODEL_OUTDOOR_CAMERA = "outdoor camera"
CAMERA_MODEL_UNKNOWN = "unknown"

MODEL_TO_TYPE = {
    "SS001": CAMERA_MODEL_CAMERA,
    "SS002": CAMERA_MODEL_DOORBELL,
    "SS003": CAMERA_MODEL_CAMERA,
    "SSOBCM4": CAMERA_MODEL_OUTDOOR_CAMERA,
}


class Camera(DeviceV3):
    """Define a SimpliCam."""

    _system: SystemV3

    @property
    def camera_settings(self) -> dict[str, Any]:
        """Return the camera settings.

        :rtype: ``dict``
        """
        return cast(
            Dict[str, Any], self._system.camera_data[self._serial]["cameraSettings"]
        )

    @property
    def camera_type(self) -> str:
        """Return the type of camera.

        :rtype: ``str``
        """
        try:
            return MODEL_TO_TYPE[self._system.camera_data[self._serial]["model"]]
        except KeyError:
            LOGGER.error(
                "Unknown camera type: %s",
                self._system.camera_data[self._serial]["model"],
            )
            return CAMERA_MODEL_UNKNOWN

    @property
    def name(self) -> str:
        """Return the camera name.

        :rtype: ``str``
        """
        return cast(
            str, self._system.camera_data[self._serial]["cameraSettings"]["cameraName"]
        )

    @property
    def serial(self) -> str:
        """Return the camera's serial number.

        :rtype: ``str``
        """
        return self._serial

    @property
    def shutter_open_when_away(self) -> bool:
        """Return whether the privacy shutter is open when the alarm is armed in away mode.

        :rtype: ``bool``
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterAway"]
        return cast(bool, val == "open")

    @property
    def shutter_open_when_home(self) -> bool:
        """Return whether the privacy shutter is open when the alarm is armed in home mode.

        :rtype: ``bool``
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterHome"]
        return cast(bool, val == "open")

    @property
    def shutter_open_when_off(self) -> bool:
        """Return whether the privacy shutter is open when the alarm is disarmed.

        :rtype: ``bool``
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterOff"]
        return cast(bool, val == "open")

    @property
    def status(self) -> str:
        """Return the camera status.

        :rtype: ``str``
        """
        return cast(str, self._system.camera_data[self._serial]["status"])

    @property
    def subscription_enabled(self) -> bool:
        """Return the camera subscription status.

        :rtype: ``bool``
        """
        return cast(
            bool, self._system.camera_data[self._serial]["subscription"]["enabled"]
        )

    def video_url(
        self,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        **kwargs: dict[str, Any],
    ) -> str:
        """Return the camera video URL.

        :rtype: ``str``
        """
        url_params = {"x": width, "audioEncoding": audio_encoding, **kwargs}
        return f"{MEDIA_URL_BASE}/{self.serial}/flv?{urlencode(url_params)}"
