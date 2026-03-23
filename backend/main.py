from __future__ import annotations

import asyncio
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, time as datetime_time, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from .database import async_session, get_db, init_db
from .errors import ErrorCode
from .logger import LogContext, logger
from .models import AutoQuest, GpLedger, Room, RoomMember, TodoItem, User, get_current_timestamp
from .security import rate_limiter, sanitize_text
from .telemetry import metrics


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await ensure_seed_data()
    keep_alive = asyncio.create_task(keep_alive_task())
    cleanup = asyncio.create_task(cleanup_expired_rooms_task())
    try:
        yield
    finally:
        keep_alive.cancel()
        cleanup.cancel()


app = FastAPI(lifespan=lifespan)

cors_allow_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "*",
    ).split(",")
    if origin.strip()
]
cors_allow_credentials = "*" not in cors_allow_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_USERS_PER_ROOM = 50
MAX_ITEMS_PER_ROOM = 200
MAX_AUTO_QUESTS_PER_ROOM = 50
MAX_ITEM_LENGTH = 500
EVENT_HISTORY_LIMIT = 100
KEEP_ALIVE_INTERVAL = 30
CLEANUP_INTERVAL = 3600
ROOM_TTL = 24 * 3600 * 1000

DAY_ORDER = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
DAY_TO_INDEX = {day: index for index, day in enumerate(DAY_ORDER)}
RANK_THRESHOLDS = (
    ("S", 1200),
    ("A", 600),
    ("B", 200),
    ("C", 0),
)

SEED_ROOM = {
    "room_code": "9999",
    "title": "我的房间",
    "timezone": "Asia/Shanghai",
}
SEED_USERS = (
    {
        "name": "vincent",
        "display_name": "Vincent",
        "avatar_url": "/cat.png",
    },
    {
        "name": "cindy",
        "display_name": "Cindy",
        "avatar_url": "/dog.png",
    },
)


class RoomAccessRequest(BaseModel):
    roomId: str
    name: str


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, List[dict]] = {}

    async def connect(self, websocket: WebSocket, room_code: str, user_id: str, user_name: str) -> None:
        await websocket.accept()
        room_connections = self.active_connections.setdefault(room_code, [])
        if len(room_connections) >= MAX_USERS_PER_ROOM:
            await websocket.close(code=4003, reason="Room is full")
            logger.warning("Connection rejected: room is full", extra={"error_code": ErrorCode.ROOM_FULL})
            raise WebSocketDisconnect

        room_connections.append(
            {
                "ws": websocket,
                "user_id": user_id,
                "user_name": user_name,
            }
        )
        metrics.increment_connections()

    def disconnect(self, websocket: WebSocket, room_code: str) -> None:
        if room_code not in self.active_connections:
            return

        before = len(self.active_connections[room_code])
        self.active_connections[room_code] = [
            connection for connection in self.active_connections[room_code] if connection["ws"] is not websocket
        ]
        if len(self.active_connections[room_code]) < before:
            metrics.decrement_connections()

        if not self.active_connections[room_code]:
            del self.active_connections[room_code]
            room_event_cache.pop(room_code, None)

    def get_connections(self, room_code: str) -> List[dict]:
        return list(self.active_connections.get(room_code, []))

    def online_user_ids(self, room_code: str) -> set[str]:
        return {connection["user_id"] for connection in self.active_connections.get(room_code, [])}


manager = ConnectionManager()
room_event_cache: Dict[str, deque] = {}


def normalize_member_name(name: str) -> str:
    return (name or "").strip().lower()


def parse_event_message(data: dict) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
    if not isinstance(data, dict):
        return None, None, None
    event_type = data.get("type")
    payload = data.get("payload")
    if not event_type or not isinstance(payload, dict):
        return None, None, None
    return event_type, payload, payload.get("clientEventId")


def sanitize_title(value: Optional[str]) -> str:
    return sanitize_text(value or "").strip()


def validate_reward_gp(value: object) -> int:
    if value is None or value == "":
        return 10
    try:
        reward = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Reward GP must be a number.") from exc
    if reward < 1 or reward > 999:
        raise ValueError("Reward GP must be between 1 and 999.")
    return reward


def repeat_days_to_mask(days: List[str]) -> int:
    if not isinstance(days, list):
        raise ValueError("Repeat days must be an array.")

    mask = 0
    for day in days:
        normalized = str(day)
        if normalized not in DAY_TO_INDEX:
            raise ValueError("Repeat days must use Sun/Mon/Tue/Wed/Thu/Fri/Sat.")
        mask |= 1 << DAY_TO_INDEX[normalized]
    return mask


def repeat_mask_to_days(mask: int) -> List[str]:
    return [day for index, day in enumerate(DAY_ORDER) if mask & (1 << index)]


def room_local_now(timezone_name: str) -> datetime:
    return datetime.now(ZoneInfo(timezone_name))


def room_today_context(timezone_name: str) -> tuple[datetime, str, str]:
    local_now = room_local_now(timezone_name)
    weekday = DAY_ORDER[(local_now.weekday() + 1) % 7]
    return local_now, local_now.date().isoformat(), weekday


def rank_for_total_gp(total_gp: int) -> str:
    for rank, threshold in RANK_THRESHOLDS:
        if total_gp >= threshold:
            return rank
    return "C"


def start_of_local_day(local_dt: datetime) -> datetime:
    return datetime.combine(local_dt.date(), datetime_time.min, tzinfo=local_dt.tzinfo)


def serialize_member(member: RoomMember, online_user_ids: set[str]) -> dict:
    user = member.user
    return {
        "userId": user.id,
        "name": user.name,
        "displayName": user.display_name,
        "avatarUrl": user.avatar_url,
        "role": member.role,
        "isOnline": user.id in online_user_ids,
    }


def serialize_auto_quest(auto_quest: AutoQuest) -> dict:
    return {
        "id": auto_quest.id,
        "title": auto_quest.title,
        "rewardGp": auto_quest.reward_gp,
        "repeatDays": repeat_mask_to_days(auto_quest.repeat_mask),
        "isEnabled": auto_quest.is_enabled,
        "createdBy": auto_quest.created_by_user.name if auto_quest.created_by_user else None,
        "createdAt": auto_quest.created_at,
        "updatedAt": auto_quest.updated_at,
    }


def serialize_todo_item(item: TodoItem, users_by_id: Dict[str, User]) -> dict:
    created_by = users_by_id.get(item.created_by_user_id)
    completed_by = users_by_id.get(item.completed_by_user_id) if item.completed_by_user_id else None
    return {
        "id": item.id,
        "title": item.title,
        "done": item.done,
        "rewardGp": item.reward_gp,
        "sourceType": item.source_type,
        "autoQuestId": item.auto_quest_id,
        "scheduledDate": item.scheduled_date,
        "createdBy": created_by.name if created_by else None,
        "completedBy": completed_by.name if completed_by else None,
        "completedAt": item.completed_at,
        "createdAt": item.created_at,
        "updatedAt": item.updated_at,
    }


def visible_room_items(items: List[TodoItem], today_str: str) -> List[TodoItem]:
    visible: List[TodoItem] = []
    for item in items:
        if item.is_deleted:
            continue
        if item.source_type == "auto_quest":
            if item.scheduled_date == today_str:
                visible.append(item)
            continue
        visible.append(item)
    return sorted(visible, key=lambda item: (item.done, item.created_at))


async def send_error_message(websocket: WebSocket, message: str) -> None:
    await websocket.send_json({"type": "error", "payload": {"message": message}})


async def load_room_member(session: AsyncSession, room_code: str, user_name: str) -> Optional[RoomMember]:
    statement = (
        select(RoomMember)
        .join(Room, RoomMember.room_id == Room.id)
        .join(User, RoomMember.user_id == User.id)
        .where(Room.room_code == room_code, User.name == user_name)
        .options(selectinload(RoomMember.user), selectinload(RoomMember.room))
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def load_room_state(session: AsyncSession, room_code: str) -> Optional[Room]:
    statement = (
        select(Room)
        .where(Room.room_code == room_code)
        .options(
            selectinload(Room.members).selectinload(RoomMember.user),
            selectinload(Room.items),
            selectinload(Room.auto_quests).selectinload(AutoQuest.created_by_user),
        )
    )
    result = await session.execute(statement)
    room = result.scalars().first()
    if not room:
        return None

    # Populate item users with two targeted reads instead of relationship fan-out.
    user_ids = {
        item.created_by_user_id
        for item in room.items
        if item.created_by_user_id
    } | {
        item.completed_by_user_id
        for item in room.items
        if item.completed_by_user_id
    }
    if user_ids:
        user_result = await session.execute(select(User).where(User.id.in_(user_ids)))
        users = {user.id: user for user in user_result.scalars().all()}
        for item in room.items:
            item.created_by_user = users.get(item.created_by_user_id)
            item.completed_by_user = users.get(item.completed_by_user_id) if item.completed_by_user_id else None
    return room


async def ensure_seed_data() -> None:
    async with async_session() as session:
        room_result = await session.execute(select(Room).where(Room.room_code == SEED_ROOM["room_code"]))
        room = room_result.scalars().first()
        if not room:
            room = Room(
                room_code=SEED_ROOM["room_code"],
                title=SEED_ROOM["title"],
                timezone=SEED_ROOM["timezone"],
                is_seeded=True,
                never_expires=True,
            )
            session.add(room)
            await session.flush()
        else:
            room.title = SEED_ROOM["title"]
            room.timezone = SEED_ROOM["timezone"]
            room.is_seeded = True
            room.never_expires = True
            room.updated_at = get_current_timestamp()
            session.add(room)

        users_by_name: Dict[str, User] = {}
        for seed_user in SEED_USERS:
            user_result = await session.execute(select(User).where(User.name == seed_user["name"]))
            user = user_result.scalars().first()
            if not user:
                user = User(**seed_user)
            else:
                user.display_name = seed_user["display_name"]
                user.avatar_url = seed_user["avatar_url"]
                user.updated_at = get_current_timestamp()
            session.add(user)
            await session.flush()
            users_by_name[user.name] = user

        for user in users_by_name.values():
            membership_result = await session.execute(
                select(RoomMember).where(RoomMember.room_id == room.id, RoomMember.user_id == user.id)
            )
            membership = membership_result.scalars().first()
            if not membership:
                membership = RoomMember(room_id=room.id, user_id=user.id, role="admin")
            else:
                membership.role = "admin"
            session.add(membership)

        await session.commit()


async def ensure_today_auto_quests(session: AsyncSession, room: Room) -> bool:
    _, today_str, weekday = room_today_context(room.timezone)
    has_changes = False

    existing_today_keys = {
        (item.auto_quest_id, item.scheduled_date)
        for item in room.items
        if item.auto_quest_id and item.scheduled_date
    }

    for auto_quest in room.auto_quests:
        if not auto_quest.is_enabled:
            continue
        if not auto_quest.repeat_mask & (1 << DAY_TO_INDEX[weekday]):
            continue
        if (auto_quest.id, today_str) in existing_today_keys:
            continue
        if len([item for item in room.items if not item.is_deleted]) >= MAX_ITEMS_PER_ROOM:
            break

        new_item = TodoItem(
            room_id=room.id,
            title=auto_quest.title,
            reward_gp=auto_quest.reward_gp,
            source_type="auto_quest",
            auto_quest_id=auto_quest.id,
            scheduled_date=today_str,
            created_by_user_id=auto_quest.created_by_user_id,
        )
        session.add(new_item)
        room.items.append(new_item)
        existing_today_keys.add((auto_quest.id, today_str))
        has_changes = True

    if has_changes:
        timestamp = get_current_timestamp()
        room.updated_at = timestamp
        room.last_activity_at = timestamp
        session.add(room)

    return has_changes


async def load_or_build_snapshot(session: AsyncSession, room_code: str) -> Optional[tuple[dict, Dict[str, dict]]]:
    room = await load_room_state(session, room_code)
    if not room:
        return None

    generated = await ensure_today_auto_quests(session, room)
    if generated:
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
        room = await load_room_state(session, room_code)
        if not room:
            return None

    _, today_str, _ = room_today_context(room.timezone)
    online_user_ids = manager.online_user_ids(room_code)
    members = [serialize_member(member, online_user_ids) for member in sorted(room.members, key=lambda member: member.created_at)]
    users_by_id = {member.user.id: member.user for member in room.members}
    items = [serialize_todo_item(item, users_by_id) for item in visible_room_items(room.items, today_str)]
    auto_quests = [serialize_auto_quest(auto_quest) for auto_quest in sorted(room.auto_quests, key=lambda quest: quest.created_at)]

    current_users = {member["userId"]: member for member in members}
    common_payload = {
        "room": {
            "roomId": room.room_code,
            "title": room.title,
            "timezone": room.timezone,
        },
        "members": members,
        "items": items,
        "autoQuests": auto_quests,
    }
    return common_payload, current_users


async def emit_room_snapshot(room_code: str, connections: Optional[List[dict]] = None) -> None:
    target_connections = connections or manager.get_connections(room_code)
    if not target_connections:
        return

    async with async_session() as session:
        snapshot = await load_or_build_snapshot(session, room_code)
        if not snapshot:
            return
        common_payload, current_users = snapshot

    for connection in target_connections:
        current_user = current_users.get(connection["user_id"])
        if not current_user:
            continue
        try:
            await connection["ws"].send_json(
                {
                    "type": "snapshot",
                    "payload": {
                        **common_payload,
                        "currentUser": current_user,
                    },
                }
            )
        except Exception:
            metrics.track_broadcast_error()


async def reverse_active_ledger(session: AsyncSession, item: TodoItem, timestamp: int) -> None:
    ledger_result = await session.execute(
        select(GpLedger)
        .where(GpLedger.todo_item_id == item.id, GpLedger.reversed_at.is_(None))
        .order_by(GpLedger.awarded_at.desc())
    )
    active_entry = ledger_result.scalars().first()
    if active_entry:
        active_entry.reversed_at = timestamp
        session.add(active_entry)


async def award_gp(session: AsyncSession, room: Room, item: TodoItem, user_id: str, timestamp: int) -> None:
    ledger_result = await session.execute(
        select(GpLedger)
        .where(
            GpLedger.todo_item_id == item.id,
            GpLedger.user_id == user_id,
            GpLedger.reversed_at.is_not(None),
        )
        .order_by(GpLedger.awarded_at.desc())
    )
    reusable_entry = ledger_result.scalars().first()
    if reusable_entry:
        reusable_entry.gp_delta = item.reward_gp
        reusable_entry.todo_title = item.title
        reusable_entry.awarded_at = timestamp
        reusable_entry.reversed_at = None
        session.add(reusable_entry)
        return

    session.add(
        GpLedger(
            room_id=room.id,
            user_id=user_id,
            todo_item_id=item.id,
            todo_title=item.title,
            gp_delta=item.reward_gp,
            awarded_at=timestamp,
        )
    )


def apply_item_edit(target: TodoItem, raw_title: Optional[str], reward_gp: Optional[int], updated_at: int) -> bool:
    updated = False

    if raw_title is not None:
        title = sanitize_title(raw_title)
        if title and title != target.title:
            target.title = title[:MAX_ITEM_LENGTH]
            updated = True

    if reward_gp is not None and reward_gp != target.reward_gp:
        target.reward_gp = reward_gp
        updated = True

    if updated:
        target.updated_at = updated_at

    return updated


async def sync_today_item_with_auto_quest(session: AsyncSession, room: Room, auto_quest: AutoQuest) -> None:
    _, today_str, _ = room_today_context(room.timezone)
    item_result = await session.execute(
        select(TodoItem).where(
            TodoItem.room_id == room.id,
            TodoItem.auto_quest_id == auto_quest.id,
            TodoItem.scheduled_date == today_str,
        )
    )
    today_item = item_result.scalars().first()
    if not today_item or today_item.is_deleted:
        return

    today_item.title = auto_quest.title
    today_item.reward_gp = auto_quest.reward_gp
    today_item.updated_at = get_current_timestamp()
    session.add(today_item)


async def keep_alive_task() -> None:
    while True:
        await asyncio.sleep(KEEP_ALIVE_INTERVAL)
        for room_code, connections in list(manager.active_connections.items()):
            if not connections:
                continue
            for connection in list(connections):
                try:
                    await connection["ws"].send_json(
                        {
                            "type": "ping",
                            "payload": {"ts": get_current_timestamp()},
                        }
                    )
                except Exception:
                    pass


async def cleanup_expired_rooms_task() -> None:
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        try:
            threshold = get_current_timestamp() - ROOM_TTL
            async with async_session() as session:
                result = await session.execute(
                    select(Room).where(Room.never_expires.is_(False), Room.last_activity_at < threshold)
                )
                expired_rooms = result.scalars().all()
                for room in expired_rooms:
                    for connection in manager.get_connections(room.room_code):
                        await connection["ws"].close(code=4004, reason="Room expired")
                    await session.delete(room)
                if expired_rooms:
                    await session.commit()
        except Exception:
            logger.error("Cleanup task failed", exc_info=True)

@app.get("/")
async def get_root() -> dict:
    return {"message": "ShareList Backend is running", "status": "ok"}


@app.get("/sys/stats")
async def get_system_stats() -> dict:
    return metrics.get_stats()


@app.post("/api/rooms/access")
async def access_room(payload: RoomAccessRequest, session: AsyncSession = Depends(get_db)) -> dict:
    room_code = (payload.roomId or "").strip()
    user_name = normalize_member_name(payload.name)

    if not room_code:
        raise HTTPException(status_code=400, detail="Room ID is required.")
    if not user_name:
        raise HTTPException(status_code=400, detail="Name is required.")

    member = await load_room_member(session, room_code, user_name)
    if not member:
        room_exists = await session.execute(select(Room).where(Room.room_code == room_code))
        if room_exists.scalars().first():
            raise HTTPException(status_code=401, detail="Only approved members can enter this room.")
        raise HTTPException(status_code=404, detail="Room not found.")

    return {
        "room": {
            "roomId": member.room.room_code,
            "title": member.room.title,
            "timezone": member.room.timezone,
        },
        "user": serialize_member(member, set()),
    }


@app.get("/api/rooms/{room_id}/snapshot")
async def get_room_snapshot(room_id: str, name: str, session: AsyncSession = Depends(get_db)) -> dict:
    normalized_name = normalize_member_name(name)
    if not normalized_name:
        raise HTTPException(status_code=400, detail="Name is required.")

    member = await load_room_member(session, room_id, normalized_name)
    if not member:
        room_exists = await session.execute(select(Room).where(Room.room_code == room_id))
        if room_exists.scalars().first():
            raise HTTPException(status_code=401, detail="Only approved members can enter this room.")
        raise HTTPException(status_code=404, detail="Room not found.")

    snapshot = await load_or_build_snapshot(session, room_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Room not found.")

    common_payload, current_users = snapshot
    current_user = current_users.get(member.user.id)
    if not current_user:
        current_user = serialize_member(member, manager.online_user_ids(room_id))

    return {
        **common_payload,
        "currentUser": current_user,
    }


@app.get("/api/rooms/{room_id}/profiles/{user_id}")
async def get_profile(room_id: str, user_id: str, session: AsyncSession = Depends(get_db)) -> dict:
    room_result = await session.execute(select(Room).where(Room.room_code == room_id))
    room = room_result.scalars().first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")

    member_result = await session.execute(
        select(RoomMember)
        .where(RoomMember.room_id == room.id, RoomMember.user_id == user_id)
        .options(selectinload(RoomMember.user))
    )
    member = member_result.scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Profile not found.")

    entries_result = await session.execute(
        select(GpLedger)
        .where(GpLedger.room_id == room.id, GpLedger.user_id == user_id, GpLedger.reversed_at.is_(None))
        .order_by(GpLedger.awarded_at.desc())
    )
    entries = entries_result.scalars().all()

    local_now = room_local_now(room.timezone)
    week_start = start_of_local_day(local_now - timedelta(days=local_now.weekday()))
    month_start = start_of_local_day(local_now.replace(day=1))
    week_start_ms = int(week_start.timestamp() * 1000)
    month_start_ms = int(month_start.timestamp() * 1000)

    total_gp = sum(entry.gp_delta for entry in entries)
    week_entries = [entry for entry in entries if entry.awarded_at >= week_start_ms]
    month_entries = [entry for entry in entries if entry.awarded_at >= month_start_ms]

    return {
        "userId": member.user.id,
        "name": member.user.name,
        "displayName": member.user.display_name,
        "avatarUrl": member.user.avatar_url,
        "rank": rank_for_total_gp(total_gp),
        "totalGp": total_gp,
        "thisWeekGp": sum(entry.gp_delta for entry in week_entries),
        "thisWeekCount": len(week_entries),
        "thisMonthGp": sum(entry.gp_delta for entry in month_entries),
        "thisMonthCount": len(month_entries),
        "history": [
            {
                "id": entry.id,
                "todoItemId": entry.todo_item_id,
                "todoTitle": entry.todo_title,
                "gpDelta": entry.gp_delta,
                "awardedAt": entry.awarded_at,
            }
            for entry in entries
        ],
    }


@app.websocket("/ws/{room_id}/{user_name}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_name: str,
    reconnect: Optional[str] = Query(None),
) -> None:
    del reconnect
    connection_id = str(uuid4())
    normalized_name = normalize_member_name(user_name)

    with LogContext(room_id=room_id, user=normalized_name, conn_id=connection_id):
        async with async_session() as session:
            member = await load_room_member(session, room_id, normalized_name)
            if not member:
                room_result = await session.execute(select(Room).where(Room.room_code == room_id))
                if room_result.scalars().first():
                    await websocket.close(code=4001, reason="Unauthorized")
                else:
                    await websocket.close(code=4004, reason="Room not found")
                return

        try:
            await manager.connect(websocket, room_id, member.user.id, member.user.name)
        except WebSocketDisconnect:
            return

        await emit_room_snapshot(room_id, manager.get_connections(room_id))

        if room_id not in room_event_cache:
            room_event_cache[room_id] = deque(maxlen=EVENT_HISTORY_LIMIT)

        try:
            while True:
                data = await websocket.receive_json()
                event_type, payload, client_event_id = parse_event_message(data)
                if not event_type or payload is None:
                    continue

                if event_type == "pong":
                    continue

                metrics.track_event()

                if client_event_id and client_event_id in room_event_cache.get(room_id, []):
                    continue

                if not rate_limiter.check_limit(f"{room_id}:{member.user.id}"):
                    await send_error_message(websocket, "You are doing that too fast.")
                    continue

                updated = False
                should_refresh = False
                db_start = time.time()

                async with async_session() as session:
                    room = await load_room_state(session, room_id)
                    if not room:
                        await websocket.close(code=4004, reason="Room not found")
                        return

                    timestamp = get_current_timestamp()

                    if event_type == "item_add":
                        title = sanitize_title(payload.get("title") or payload.get("text"))
                        if not title:
                            await send_error_message(websocket, "Quest name is required.")
                            continue

                        active_items = [item for item in room.items if not item.is_deleted]
                        if len(active_items) >= MAX_ITEMS_PER_ROOM:
                            await send_error_message(websocket, "Room limit reached.")
                            continue

                        try:
                            reward_gp = validate_reward_gp(payload.get("rewardGp"))
                        except ValueError as exc:
                            await send_error_message(websocket, str(exc))
                            continue

                        session.add(
                            TodoItem(
                                room_id=room.id,
                                title=title[:MAX_ITEM_LENGTH],
                                reward_gp=reward_gp,
                                source_type="manual",
                                created_by_user_id=member.user.id,
                            )
                        )
                        updated = True

                    elif event_type == "item_edit":
                        item_id = payload.get("itemId")
                        target = next((item for item in room.items if item.id == item_id and not item.is_deleted), None)
                        if not target:
                            await send_error_message(websocket, "Quest not found.")
                            continue

                        reward_gp = None
                        if "rewardGp" in payload:
                            try:
                                reward_gp = validate_reward_gp(payload.get("rewardGp"))
                            except ValueError as exc:
                                await send_error_message(websocket, str(exc))
                                continue

                        changed = apply_item_edit(
                            target,
                            payload.get("title") or payload.get("text"),
                            reward_gp,
                            timestamp,
                        )
                        if changed:
                            session.add(target)
                            if target.done:
                                ledger_result = await session.execute(
                                    select(GpLedger)
                                    .where(GpLedger.todo_item_id == target.id, GpLedger.reversed_at.is_(None))
                                )
                                for entry in ledger_result.scalars().all():
                                    entry.gp_delta = target.reward_gp
                                    entry.todo_title = target.title
                                    session.add(entry)
                            if target.auto_quest_id:
                                auto_quest = next((quest for quest in room.auto_quests if quest.id == target.auto_quest_id), None)
                                if auto_quest and target.scheduled_date == room_today_context(room.timezone)[1]:
                                    auto_quest.title = target.title
                                    auto_quest.reward_gp = target.reward_gp
                                    auto_quest.updated_at = timestamp
                                    session.add(auto_quest)
                            updated = True

                    elif event_type == "item_toggle":
                        item_id = payload.get("itemId")
                        done = bool(payload.get("done"))
                        target = next((item for item in room.items if item.id == item_id and not item.is_deleted), None)
                        if not target:
                            await send_error_message(websocket, "Quest not found.")
                            continue

                        if target.done == done:
                            continue

                        target.done = done
                        target.updated_at = timestamp
                        if done:
                            target.completed_by_user_id = member.user.id
                            target.completed_at = timestamp
                            await award_gp(session, room, target, member.user.id, timestamp)
                        else:
                            target.completed_by_user_id = None
                            target.completed_at = None
                            await reverse_active_ledger(session, target, timestamp)
                        session.add(target)
                        updated = True

                    elif event_type == "item_delete":
                        item_id = payload.get("itemId")
                        target = next((item for item in room.items if item.id == item_id and not item.is_deleted), None)
                        if not target:
                            await send_error_message(websocket, "Quest not found.")
                            continue

                        target.is_deleted = True
                        target.updated_at = timestamp
                        session.add(target)
                        updated = True

                    elif event_type == "auto_quest_create":
                        title = sanitize_title(payload.get("title"))
                        if not title:
                            await send_error_message(websocket, "Auto Quest name is required.")
                            continue

                        if len(room.auto_quests) >= MAX_AUTO_QUESTS_PER_ROOM:
                            await send_error_message(websocket, "Auto Quest limit reached.")
                            continue

                        try:
                            reward_gp = validate_reward_gp(payload.get("rewardGp"))
                            repeat_mask = repeat_days_to_mask(payload.get("repeatDays") or [])
                        except ValueError as exc:
                            await send_error_message(websocket, str(exc))
                            continue

                        if repeat_mask == 0:
                            await send_error_message(websocket, "Pick at least one repeat day.")
                            continue

                        session.add(
                            AutoQuest(
                                room_id=room.id,
                                title=title[:MAX_ITEM_LENGTH],
                                reward_gp=reward_gp,
                                repeat_mask=repeat_mask,
                                is_enabled=bool(payload.get("isEnabled", True)),
                                created_by_user_id=member.user.id,
                            )
                        )
                        updated = True
                        should_refresh = True

                    elif event_type == "auto_quest_update":
                        auto_quest_id = payload.get("autoQuestId")
                        target = next((quest for quest in room.auto_quests if quest.id == auto_quest_id), None)
                        if not target:
                            await send_error_message(websocket, "Auto Quest not found.")
                            continue

                        if "title" in payload:
                            title = sanitize_title(payload.get("title"))
                            if not title:
                                await send_error_message(websocket, "Auto Quest name is required.")
                                continue
                            target.title = title[:MAX_ITEM_LENGTH]

                        if "rewardGp" in payload:
                            try:
                                target.reward_gp = validate_reward_gp(payload.get("rewardGp"))
                            except ValueError as exc:
                                await send_error_message(websocket, str(exc))
                                continue

                        if "repeatDays" in payload:
                            try:
                                repeat_mask = repeat_days_to_mask(payload.get("repeatDays") or [])
                            except ValueError as exc:
                                await send_error_message(websocket, str(exc))
                                continue
                            if repeat_mask == 0:
                                await send_error_message(websocket, "Pick at least one repeat day.")
                                continue
                            target.repeat_mask = repeat_mask

                        if "isEnabled" in payload:
                            target.is_enabled = bool(payload.get("isEnabled"))

                        target.updated_at = timestamp
                        session.add(target)
                        await sync_today_item_with_auto_quest(session, room, target)
                        updated = True
                        should_refresh = True

                    elif event_type == "auto_quest_toggle":
                        auto_quest_id = payload.get("autoQuestId")
                        target = next((quest for quest in room.auto_quests if quest.id == auto_quest_id), None)
                        if not target:
                            await send_error_message(websocket, "Auto Quest not found.")
                            continue
                        target.is_enabled = bool(payload.get("isEnabled"))
                        target.updated_at = timestamp
                        session.add(target)
                        updated = True
                        should_refresh = True

                    else:
                        await send_error_message(websocket, "Unsupported event.")
                        continue

                    if not updated:
                        continue

                    room.updated_at = timestamp
                    room.last_activity_at = timestamp
                    session.add(room)
                    await session.commit()
                    metrics.track_db_latency(db_start, is_write=True)

                if client_event_id:
                    room_event_cache.setdefault(room_id, deque(maxlen=EVENT_HISTORY_LIMIT)).append(client_event_id)

                if should_refresh:
                    async with async_session() as refresh_session:
                        refreshed_room = await load_room_state(refresh_session, room_id)
                        if refreshed_room:
                            await ensure_today_auto_quests(refresh_session, refreshed_room)
                            await refresh_session.commit()

                await emit_room_snapshot(room_id)

        except WebSocketDisconnect:
            manager.disconnect(websocket, room_id)
            await emit_room_snapshot(room_id)
        except Exception:
            logger.error("Unexpected websocket error", exc_info=True)
            metrics.track_error()
            manager.disconnect(websocket, room_id)
            await emit_room_snapshot(room_id)
