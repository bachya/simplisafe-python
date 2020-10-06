import logging
from urllib.parse import urlencode

from simplipy.entity import Entity

_LOGGER: logging.Logger = logging.getLogger(__name__)

MEDIA_URL_BASE: str = "https://media.simplisafe.com/v1"
DEFAULT_VIDEO_WIDTH: int = 1280
DEFAULT_AUDIO_ENCODING: str = "AAC"

CAMERA_MODEL_CAMERA: str = "CAMERA"
CAMERA_MODEL_DOORBELL: str = "DOORBELL"
CAMERA_MODEL_UNKNOWN: str = "CAMERA_MODEL_UNKNOWN"

MODEL_TO_TYPE = {
    "SS001": CAMERA_MODEL_CAMERA,
    "SS002": CAMERA_MODEL_DOORBELL,
    "unknown": CAMERA_MODEL_UNKNOWN,
}


class Camera(Entity):
    """A SimpliCam."""

    @property
    def camera_settings(self) -> dict:
        """Return the camera settings.

        :rtype: ``dict``
        """
        return self.entity_data["cameraSettings"]

    @property
    def camera_type(self) -> str:
        """Return the type of camera.

        :rtype: ``str``
        """

        try:
            return MODEL_TO_TYPE[self.entity_data["model"]]
        except KeyError:
            _LOGGER.error("Unknown camera type: %s", self.entity_data["model"])
            return MODEL_TO_TYPE["unknown"]

    @property
    def name(self) -> str:
        """Return the entity name.

        :rtype: ``str``
        """
        return self.entity_data["cameraSettings"]["cameraName"]

    @property
    def serial(self) -> str:
        """Return the entity's serial number.

        :rtype: ``str``
        """
        return self.entity_data["uuid"]

    @property
    def shutter_open_when_away(self) -> bool:
        """Return whether the privacy shutter is open when alarm system is armed in away mode.

        :rtype: ``bool``
        """
        return self.camera_settings["shutterAway"] == "open"

    @property
    def shutter_open_when_home(self) -> bool:
        """Return whether the privacy shutter is open when alarm system is armed in home mode.

        :rtype: ``bool``
        """
        return self.camera_settings["shutterHome"] == "open"

    @property
    def shutter_open_when_off(self) -> bool:
        """Return whether the privacy shutter is open when alarm system is off.

        :rtype: ``bool``
        """
        return self.camera_settings["shutterOff"] == "open"

    @property
    def status(self) -> str:
        """Return the camera status.

        :rtype: ``str``
        """
        return self.entity_data["status"]

    @property
    def subscription_enabled(self) -> bool:
        """Return the camera subscription status.

        :rtype: ``bool``
        """
        return self.entity_data["subscription"]["enabled"]

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
