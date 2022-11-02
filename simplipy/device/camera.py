"""Define SimpliSafe cameras (SimpliCams)."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlencode

from simplipy.const import LOGGER
from simplipy.device import DeviceV3

if TYPE_CHECKING:
    from simplipy.system.v3 import SystemV3

DEFAULT_AUDIO_ENCODING = "AAC"
DEFAULT_MEDIA_URL_BASE = "https://media.simplisafe.com/v1"
DEFAULT_VIDEO_WIDTH = 1280


class CameraTypes(Enum):
    """Define camera types based on internal SimpliSafe ID number."""

    CAMERA = 0
    DOORBELL = 1
    OUTDOOR_CAMERA = 2
    UNKNOWN = 99


MODEL_TO_TYPE = {
    "SS001": CameraTypes.CAMERA,
    "SS002": CameraTypes.DOORBELL,
    "SS003": CameraTypes.CAMERA,
    "SSOBCM4": CameraTypes.OUTDOOR_CAMERA,
}


class Camera(DeviceV3):
    """Define a SimpliCam."""

    _system: SystemV3

    @property
    def camera_settings(self) -> dict[str, Any]:
        """Return the camera settings.

        Returns:
            A dictionary of camera settings.
        """
        return cast(
            dict[str, Any], self._system.camera_data[self._serial]["cameraSettings"]
        )

    @property
    def camera_type(self) -> CameraTypes:
        """Return the type of camera.

        Returns:
            The camera type.
        """
        try:
            return MODEL_TO_TYPE[self._system.camera_data[self._serial]["model"]]
        except KeyError:
            LOGGER.error(
                "Unknown camera type: %s",
                self._system.camera_data[self._serial]["model"],
            )
            return CameraTypes.UNKNOWN

    @property
    def name(self) -> str:
        """Return the camera name.

        Returns:
            The camera name.
        """
        return cast(
            str, self._system.camera_data[self._serial]["cameraSettings"]["cameraName"]
        )

    @property
    def serial(self) -> str:
        """Return the camera's serial number.

        Returns:
            The camera serial number.
        """
        return self._serial

    @property
    def shutter_open_when_away(self) -> bool:
        """Return whether the privacy shutter is open in away mode.

        Returns:
            The camera's "shutter open when away" status.
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterAway"]
        return cast(bool, val == "open")

    @property
    def shutter_open_when_home(self) -> bool:
        """Return whether the privacy shutter is open in home mode.

        Returns:
            The camera's "shutter open when home" status.
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterHome"]
        return cast(bool, val == "open")

    @property
    def shutter_open_when_off(self) -> bool:
        """Return whether the privacy shutter is open when the alarm is disarmed.

        Returns:
            The camera's "shutter open when off" status.
        """
        val = self._system.camera_data[self._serial]["cameraSettings"]["shutterOff"]
        return cast(bool, val == "open")

    @property
    def status(self) -> str:
        """Return the camera status.

        Returns:
            The camera status.
        """
        return cast(str, self._system.camera_data[self._serial]["status"])

    @property
    def subscription_enabled(self) -> bool:
        """Return the camera subscription status.

        Returns:
            The camera subscription status.
        """
        return cast(
            bool, self._system.camera_data[self._serial]["subscription"]["enabled"]
        )

    def as_dict(self) -> dict[str, Any]:
        """Return dictionary version of this device.

        Returns:
            A dict representation of this device.
        """
        return {
            "camera_settings": self.camera_settings,
            "camera_type": self.camera_type.value,
            "name": self.name,
            "serial": self.serial,
            "shutter_open_when_away": self.shutter_open_when_away,
            "shutter_open_when_home": self.shutter_open_when_home,
            "shutter_open_when_off": self.shutter_open_when_off,
            "status": self.status,
            "subscription_enabled": self.subscription_enabled,
        }

    def video_url(
        self,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        **kwargs: Any,
    ) -> str:
        """Return the camera video URL.

        Args:
            width: The video width.
            audio_encoding: The audio encoding.
            kwargs: Additional parameters.

        Returns:
            The camera video URL.
        """
        url_params = {"x": width, "audioEncoding": audio_encoding, **kwargs}
        return f"{DEFAULT_MEDIA_URL_BASE}/{self.serial}/flv?{urlencode(url_params)}"
