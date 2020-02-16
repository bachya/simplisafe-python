"""Test message helpers."""
from datetime import datetime

import pytz

from simplipy.entity import EntityTypes
from simplipy.helpers.message import Message


def test_create_message():
    """Test the successful creation of a message."""
    basic_message = Message("event", "This is a test message", 1234, 1581892842)
    assert basic_message.event == "event"
    assert basic_message.message == "This is a test message"
    assert basic_message.system_id == 1234
    assert basic_message.timestamp == datetime(2020, 2, 16, 22, 40, 42, tzinfo=pytz.UTC)
    assert not basic_message.changed_by
    assert not basic_message.sensor_name
    assert not basic_message.sensor_serial
    assert not basic_message.sensor_type

    complete_message = Message(
        "event",
        "This is a test message",
        1234,
        1581892842,
        changed_by="1234",
        sensor_name="Kitchen Window",
        sensor_serial="ABC123",
        sensor_type=5,
    )
    assert complete_message.event == "event"
    assert complete_message.message == "This is a test message"
    assert complete_message.system_id == 1234
    assert complete_message.timestamp == datetime(
        2020, 2, 16, 22, 40, 42, tzinfo=pytz.UTC
    )
    assert complete_message.changed_by == "1234"
    assert complete_message.sensor_name == "Kitchen Window"
    assert complete_message.sensor_serial == "ABC123"
    assert complete_message.sensor_type == EntityTypes.entry

    assert basic_message != complete_message


def test_unknown_sensor_type(caplog):
    """Test creating a message with an unknown sensor type."""
    message = Message(
        "event", "This is a test message", 1234, 1581892842, sensor_type="doesnt_exist"
    )

    assert any("Encountered unknown entity type" in e.message for e in caplog.records)
    assert any("doesnt_exist" in e.message for e in caplog.records)
    assert not message.sensor_type
