import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/sharelist_test")

from backend.main import apply_item_edit, cors_allow_credentials, cors_allow_origins, parse_event_message
from backend.models import TodoItem


def test_parse_event_message_handles_missing_payload():
    event_type, payload, client_event_id = parse_event_message({"type": "item_add", "payload": None})
    assert event_type is None
    assert payload is None
    assert client_event_id is None


def test_parse_event_message_extracts_client_event_id():
    event_type, payload, client_event_id = parse_event_message(
        {"type": "item_add", "payload": {"text": "hello", "clientEventId": "evt-1"}}
    )
    assert event_type == "item_add"
    assert payload == {"text": "hello", "clientEventId": "evt-1"}
    assert client_event_id == "evt-1"


def test_apply_item_edit_supports_priority_only_update():
    item = TodoItem(text="Milk", priority="medium", room_db_id="room-1")
    changed = apply_item_edit(
        target=item,
        raw_text="",
        priority="high",
        updated_at=123456789,
    )
    assert changed is True
    assert item.text == "Milk"
    assert item.priority == "high"
    assert item.updatedAt == 123456789


def test_default_cors_config_is_not_wildcard():
    assert "*" not in cors_allow_origins
    assert cors_allow_credentials is True
