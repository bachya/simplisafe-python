from simplipy.entity import Entity


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

    def video_url(self, width=1280, params={"audioEncoding": "AAC"}) -> str:
        """Return the camera video URL.

        :rtype: ``str``
        """
        additionalParams = ["{}={}".format(param, params[param]) for param in params]
        additionalParamsUrl = ""
        if additionalParams:
            additionalParamsUrl = "&{}".format("&".join(additionalParams))

        return "https://media.simplisafe.com/v1/{}/flv?x={}{}".format(
            self.serial, width, additionalParamsUrl
        )

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
