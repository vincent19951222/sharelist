import importlib
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test-sharelist.db")

import backend.main as main_module  # noqa: E402
from backend.main import (  # noqa: E402
    apply_item_edit,
    parse_event_message,
    rank_for_total_gp,
    repeat_days_to_mask,
    repeat_mask_to_days,
    validate_reward_gp,
)
from backend.models import TodoItem  # noqa: E402


def test_parse_event_message_handles_missing_payload():
    event_type, payload, client_event_id = parse_event_message({"type": "item_add", "payload": None})
    assert event_type is None
    assert payload is None
    assert client_event_id is None


def test_parse_event_message_extracts_client_event_id():
    event_type, payload, client_event_id = parse_event_message(
        {"type": "item_add", "payload": {"title": "hello", "clientEventId": "evt-1"}}
    )
    assert event_type == "item_add"
    assert payload == {"title": "hello", "clientEventId": "evt-1"}
    assert client_event_id == "evt-1"


def test_apply_item_edit_updates_reward_and_title():
    item = TodoItem(room_id="room-1", title="Milk", created_by_user_id="user-1", reward_gp=10)
    changed = apply_item_edit(
        target=item,
        raw_title="Buy almond milk",
        reward_gp=25,
        updated_at=123456789,
    )
    assert changed is True
    assert item.title == "Buy almond milk"
    assert item.reward_gp == 25
    assert item.updated_at == 123456789


def test_validate_reward_gp():
    assert validate_reward_gp(None) == 10
    assert validate_reward_gp("20") == 20


def test_validate_reward_gp_rejects_out_of_range():
    try:
        validate_reward_gp(0)
    except ValueError as exc:
        assert "between 1 and 999" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid reward")


def test_repeat_day_round_trip():
    mask = repeat_days_to_mask(["Mon", "Wed", "Fri"])
    assert repeat_mask_to_days(mask) == ["Mon", "Wed", "Fri"]


def test_rank_for_total_gp():
    assert rank_for_total_gp(0) == "C"
    assert rank_for_total_gp(200) == "B"
    assert rank_for_total_gp(600) == "A"
    assert rank_for_total_gp(1200) == "S"


def test_default_cors_config_allows_lan_dev(monkeypatch):
    previous = os.environ.get("CORS_ALLOW_ORIGINS")
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    reloaded = importlib.reload(main_module)

    try:
        assert reloaded.cors_allow_origins == ["*"]
        assert reloaded.cors_allow_credentials is False
    finally:
        if previous is None:
            monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
        else:
            monkeypatch.setenv("CORS_ALLOW_ORIGINS", previous)
        importlib.reload(main_module)
