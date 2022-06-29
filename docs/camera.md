# Cameras

{meth}`Camera <simplipy.camera.Camera>` objects correspond to SimpliSafe™ "SimpliCam"
cameras and doorbells (only available for V3 systems) and allow users to retrieve
information on them, including URLs to view short-lived streams of the camera.

## Core Properties

All {meth}`Camera <simplipy.camera.Camera>` objects come with a standard set of properties:

```python
for serial, camera in system.cameras.items():
    # Return the cammera's UUID:
    serial
    # >>> 1234ABCD

    # ...or through the property:
    camera.serial
    # >>> 1234ABCD

    # Return all camera settings data:
    camera.camera_settings
    # >>> {"cameraName": "Camera", "pictureQuality": "720p", ...}

    # Return the type of camera this object represents:
    camera.camera_type
    # >>> doorbell

    # Return the camera name:
    camera.name
    # >>> My Doorbell

    # Return whether the privacy shutter is open when the
    # alarm is armed in away mode:
    camera.shutter_open_when_off
    # >>> False

    # Return whether the privacy shutter is open when the
    # alarm is armed in home mode:
    camera.shutter_open_when_home
    # >>> False

    # Return whether the privacy shutter is open when the
    # alarm is disarmed:
    camera.shutter_open_when_off
    # >>> False

    # Return the camera status:
    camera.status
    # >>> online

    # Return the camera subscription status:
    camera.subscription_enabled
    # >>> True
```

## Getting the Camera Video URL

```python
url = camera.video_url()
# >>> https://media.simplisafe.com/v1/...
```
