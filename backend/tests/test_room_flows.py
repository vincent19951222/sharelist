import asyncio
import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _sqlite_url(db_path: Path) -> str:
    return f"sqlite+aiosqlite:///{db_path}"


@pytest.fixture
def room_app(tmp_path, monkeypatch):
    db_path = tmp_path / "room-flow.db"
    monkeypatch.setenv("DATABASE_URL", _sqlite_url(db_path))
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")

    import backend.database as database_module
    import backend.main as main_module

    database_module = importlib.reload(database_module)
    main_module = importlib.reload(main_module)

    with TestClient(main_module.app) as client:
        yield client, main_module

    asyncio.run(database_module.engine.dispose())


def receive_message_of_type(websocket, message_type: str, attempts: int = 6) -> dict:
    for _ in range(attempts):
        message = websocket.receive_json()
        if message["type"] == message_type:
            return message
    raise AssertionError(f"Did not receive {message_type} within {attempts} messages.")


def member_online(snapshot_payload: dict, name: str) -> bool:
    for member in snapshot_payload["members"]:
        if member["name"] == name:
            return bool(member["isOnline"])
    raise AssertionError(f"Member {name} not found in snapshot.")


def test_enter_room_and_http_snapshot_bootstrap(room_app):
    client, _ = room_app

    access_response = client.post("/api/rooms/access", json={"roomId": "9999", "name": "vincent"})
    assert access_response.status_code == 200
    access_payload = access_response.json()
    assert access_payload["room"]["roomId"] == "9999"
    assert access_payload["user"]["name"] == "vincent"
    assert access_payload["user"]["role"] == "admin"

    snapshot_response = client.get("/api/rooms/9999/snapshot", params={"name": "vincent"})
    assert snapshot_response.status_code == 200
    snapshot_payload = snapshot_response.json()

    assert snapshot_payload["room"] == {
        "roomId": "9999",
        "title": "我的房间",
        "timezone": "Asia/Shanghai",
    }
    assert snapshot_payload["currentUser"]["name"] == "vincent"
    assert {member["name"] for member in snapshot_payload["members"]} == {"vincent", "cindy"}
    assert snapshot_payload["items"] == []
    assert snapshot_payload["autoQuests"] == []


def test_websocket_reconnect_updates_presence(room_app):
    client, _ = room_app

    with client.websocket_connect("/ws/9999/vincent") as vincent_ws:
        first_snapshot = receive_message_of_type(vincent_ws, "snapshot")["payload"]
        assert first_snapshot["currentUser"]["name"] == "vincent"
        assert member_online(first_snapshot, "vincent") is True

    with client.websocket_connect("/ws/9999/vincent") as vincent_reconnect_ws:
        second_snapshot = receive_message_of_type(vincent_reconnect_ws, "snapshot")["payload"]
        assert second_snapshot["currentUser"]["name"] == "vincent"
        assert member_online(second_snapshot, "vincent") is True

        vincent_reconnect_ws.send_json(
            {
                "type": "item_add",
                "payload": {
                    "title": "Reconnect task",
                    "rewardGp": 10,
                    "clientEventId": "evt-reconnect-add",
                },
            }
        )
        updated_snapshot = receive_message_of_type(vincent_reconnect_ws, "snapshot")["payload"]
        assert any(item["title"] == "Reconnect task" for item in updated_snapshot["items"])


def test_auto_quest_generation_and_gp_lifecycle(room_app):
    client, main_module = room_app

    access_payload = client.post("/api/rooms/access", json={"roomId": "9999", "name": "vincent"}).json()
    vincent_user_id = access_payload["user"]["userId"]
    _, today_str, weekday = main_module.room_today_context("Asia/Shanghai")

    with client.websocket_connect("/ws/9999/vincent") as vincent_ws:
        initial_snapshot = receive_message_of_type(vincent_ws, "snapshot")["payload"]
        assert initial_snapshot["items"] == []
        assert initial_snapshot["autoQuests"] == []

        vincent_ws.send_json(
            {
                "type": "auto_quest_create",
                "payload": {
                    "title": "Water plants",
                    "rewardGp": 25,
                    "repeatDays": [weekday],
                    "clientEventId": "evt-auto-create",
                },
            }
        )
        created_snapshot = receive_message_of_type(vincent_ws, "snapshot")["payload"]
        assert len(created_snapshot["autoQuests"]) == 1
        auto_quest = created_snapshot["autoQuests"][0]
        assert auto_quest["title"] == "Water plants"
        assert auto_quest["rewardGp"] == 25
        assert auto_quest["repeatDays"] == [weekday]

        today_items = [item for item in created_snapshot["items"] if item["sourceType"] == "auto_quest"]
        assert len(today_items) == 1
        today_item = today_items[0]
        assert today_item["title"] == "Water plants"
        assert today_item["scheduledDate"] == today_str
        assert today_item["rewardGp"] == 25
        assert today_item["done"] is False

        vincent_ws.send_json(
            {
                "type": "item_toggle",
                "payload": {
                    "itemId": today_item["id"],
                    "done": True,
                    "clientEventId": "evt-item-done",
                },
            }
        )
        completed_snapshot = receive_message_of_type(vincent_ws, "snapshot")["payload"]
        completed_item = next(item for item in completed_snapshot["items"] if item["id"] == today_item["id"])
        assert completed_item["done"] is True
        assert completed_item["completedBy"] == "vincent"
        assert completed_item["completedAt"] is not None

        profile_after_complete = client.get(f"/api/rooms/9999/profiles/{vincent_user_id}")
        assert profile_after_complete.status_code == 200
        completed_profile = profile_after_complete.json()
        assert completed_profile["totalGp"] == 25
        assert completed_profile["thisWeekGp"] == 25
        assert completed_profile["history"] == [
            {
                "id": completed_profile["history"][0]["id"],
                "todoItemId": today_item["id"],
                "todoTitle": "Water plants",
                "gpDelta": 25,
                "awardedAt": completed_profile["history"][0]["awardedAt"],
            }
        ]

        vincent_ws.send_json(
            {
                "type": "item_toggle",
                "payload": {
                    "itemId": today_item["id"],
                    "done": False,
                    "clientEventId": "evt-item-undone",
                },
            }
        )
        reverted_snapshot = receive_message_of_type(vincent_ws, "snapshot")["payload"]
        reverted_item = next(item for item in reverted_snapshot["items"] if item["id"] == today_item["id"])
        assert reverted_item["done"] is False
        assert reverted_item["completedBy"] is None
        assert reverted_item["completedAt"] is None

        profile_after_revert = client.get(f"/api/rooms/9999/profiles/{vincent_user_id}")
        assert profile_after_revert.status_code == 200
        reverted_profile = profile_after_revert.json()
        assert reverted_profile["totalGp"] == 0
        assert reverted_profile["thisWeekGp"] == 0
        assert reverted_profile["thisMonthGp"] == 0
        assert reverted_profile["history"] == []
