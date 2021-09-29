"""Define common test utilities."""
import os

TEST_ACCESS_TOKEN = "abcde12345"
TEST_ADDRESS = "1234 Main Street"
TEST_AUTHORIZATION_CODE = "123abc"
TEST_CAMERA_ID = "1234567890"
TEST_CAMERA_ID_2 = "1234567891"
TEST_CODE_VERIFIER = "123abc"
TEST_LOCK_ID = "987"
TEST_LOCK_ID_2 = "654"
TEST_LOCK_ID_3 = "321"
TEST_REFRESH_TOKEN = "qrstu98765"
TEST_SUBSCRIPTION_ID = 12345
TEST_SYSTEM_ID = 12345
TEST_SYSTEM_SERIAL_NO = "1234ABCD"
TEST_USER_ID = 12345


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path, encoding="utf-8") as fptr:
        return fptr.read()
