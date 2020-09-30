from typing import Dict
from urllib.parse import urlencode

from simplipy.entity import Entity

DOORBELL_MODEL: str = "SS002"

MEDIA_URL_HOSTNAME: str = "media.simplisafe.com"
MEDIA_URL_BASE: str = f"https://{MEDIA_URL_HOSTNAME}/v1"


class Camera(Entity):
    """A SimpliCam."""

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
    def camera_settings(self) -> dict:
        """Return the camera settings.

        :rtype: ``dict``
        """
        return self.entity_data["cameraSettings"]

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

    @property
    def shutter_open_when_off(self) -> bool:
        """Return whether the privacy shutter is open when alarm system is off.

        :rtype: ``bool``
        """
        return self.camera_settings["shutterOff"] == "open"

    @property
    def shutter_open_when_home(self) -> bool:
        """Return whether the privacy shutter is open when alarm system is armed in home mode.

        :rtype: ``bool``
        """
        return self.camera_settings["shutterHome"] == "open"

    @property
    def shutter_open_when_away(self) -> bool:
        """Return whether the privacy shutter is open when alarm system is armed in away mode.

        :rtype: ``bool``
        """
        return self.camera_settings["shutterAway"] == "open"

    def video_url(
        self, width: int = 1280, audio_encoding: str = "AAC", **kwargs
    ) -> str:
        """Return the camera video URL.

        :rtype: ``str``
        """
        url_params: Dict[str, str] = {}

        if width:
            url_params["x"] = f"{width}"

        if audio_encoding:
            url_params["audioEncoding"] = audio_encoding

        for key, value in kwargs.items():
            url_params[key] = value

        return f"{MEDIA_URL_BASE}/{self.serial}/flv?{urlencode(url_params)}"
