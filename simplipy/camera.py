"""Define SimpliSafe cameras (SimpliCams)."""
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from simplipy.const import LOGGER

if TYPE_CHECKING:
    from simplipy.system.v3 import SystemV3

MEDIA_URL_BASE = "https://media.simplisafe.com/v1"
DEFAULT_VIDEO_WIDTH = 1280
DEFAULT_AUDIO_ENCODING = "AAC"

CAMERA_MODEL_CAMERA = "camera"
CAMERA_MODEL_DOORBELL = "doorbell"
CAMERA_MODEL_UNKNOWN = "unknown"

MODEL_TO_TYPE = {
    "SS001": CAMERA_MODEL_CAMERA,
    "SS002": CAMERA_MODEL_DOORBELL,
}


class Camera:
    """Define a SimpliCam."""

    def __init__(self, system: "SystemV3", uuid: str) -> None:
        """Initialize."""
        self._system = system
        self._uuid = uuid

    @property
    def camera_settings(self) -> dict:
        """Return the camera settings.

        :rtype: ``dict``
        """
        return self._system.camera_data[self._uuid]["cameraSettings"]

    @property
    def camera_type(self) -> str:
        """Return the type of camera.

        :rtype: ``str``
        """
        try:
            return MODEL_TO_TYPE[self._system.camera_data[self._uuid]["model"]]
        except KeyError:
            LOGGER.error(
                "Unknown camera type: %s", self._system.camera_data[self._uuid]["model"]
            )
            return CAMERA_MODEL_UNKNOWN

    @property
    def name(self) -> str:
        """Return the entity name.

        :rtype: ``str``
        """
        return self._system.camera_data[self._uuid]["cameraSettings"]["cameraName"]

    @property
    def serial(self) -> str:
        """Return the entity's serial number.

        :rtype: ``str``
        """
        return self._uuid

    @property
    def shutter_open_when_away(self) -> bool:
        """Return whether the privacy shutter is open when the alarm is armed in away mode.

        :rtype: ``bool``
        """
        return (
            self._system.camera_data[self._uuid]["cameraSettings"]["shutterAway"]
            == "open"
        )

    @property
    def shutter_open_when_home(self) -> bool:
        """Return whether the privacy shutter is open when the alarm is armed in home mode.

        :rtype: ``bool``
        """
        return (
            self._system.camera_data[self._uuid]["cameraSettings"]["shutterHome"]
            == "open"
        )

    @property
    def shutter_open_when_off(self) -> bool:
        """Return whether the privacy shutter is open when the alarm is disarmed.

        :rtype: ``bool``
        """
        return (
            self._system.camera_data[self._uuid]["cameraSettings"]["shutterOff"]
            == "open"
        )

    @property
    def status(self) -> str:
        """Return the camera status.

        :rtype: ``str``
        """
        return self._system.camera_data[self._uuid]["status"]

    @property
    def subscription_enabled(self) -> bool:
        """Return the camera subscription status.

        :rtype: ``bool``
        """
        return self._system.camera_data[self._uuid]["subscription"]["enabled"]

    def video_url(
        self,
        width: int = DEFAULT_VIDEO_WIDTH,
        audio_encoding: str = DEFAULT_AUDIO_ENCODING,
        **kwargs,
    ) -> str:
        """Return the camera video URL.

        :rtype: ``str``
        """
        url_params = {"x": width, "audioEncoding": audio_encoding, **kwargs}
        return f"{MEDIA_URL_BASE}/{self.serial}/flv?{urlencode(url_params)}"
