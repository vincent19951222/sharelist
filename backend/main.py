from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Tuple
import asyncio
import os
import time
from uuid import uuid4
from collections import deque
from nanoid import generate

from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .database import init_db, get_db, async_session
from .models import Room, TodoItem, RoomCreate
from .logger import logger, LogContext
from .errors import ErrorCode
from .telemetry import metrics
from .security import sanitize_text, rate_limiter

app = FastAPI()

cors_allow_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
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

@app.get("/")
async def get_root():
    return {"message": "ShareList Backend is running (With Auth)", "status": "ok"}

@app.get("/sys/stats")
async def get_system_stats():
    """Lightweight observability endpoint"""
    return metrics.get_stats()

# Configuration
MAX_USERS_PER_ROOM = 50
MAX_ITEMS_PER_ROOM = 200
MAX_ITEM_LENGTH = 500
EVENT_HISTORY_LIMIT = 100
KEEP_ALIVE_INTERVAL = 30  # seconds

# Priority validation
VALID_PRIORITIES = {"high", "medium", "low"}

def validate_priority(priority: Optional[str]) -> str:
    """
    Validate and return priority value.
    Defaults to 'medium' if None.
    Raises ValueError if invalid priority is provided.
    """
    if priority is None:
        return "medium"
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority: '{priority}'. Use: high, medium, or low")
    return priority

# In-memory Idempotency Cache (per room)
room_event_cache: Dict[str, deque] = {}

def parse_event_message(data: dict) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
    """
    Parse websocket message and safely extract event metadata.
    Returns (event_type, payload_dict, client_event_id).
    """
    if not isinstance(data, dict):
        return None, None, None
    event_type = data.get("type")
    payload = data.get("payload")
    if not event_type or not isinstance(payload, dict):
        return None, None, None
    return event_type, payload, payload.get("clientEventId")

def apply_item_edit(target: TodoItem, raw_text: Optional[str], priority: Optional[str], updated_at: int) -> bool:
    """
    Apply optional text/priority updates to a TodoItem.
    Returns True when any field changes.
    """
    updated = False

    # Only update text when a non-empty value is provided after sanitization.
    if raw_text is not None:
        text = sanitize_text(raw_text)
        if text and target.text != text:
            target.text = text[:MAX_ITEM_LENGTH]
            target.updatedAt = updated_at
            updated = True

    if priority is not None and target.priority != priority:
        target.priority = priority
        target.updatedAt = updated_at
        updated = True

    return updated

# Connection Manager
class ConnectionManager:
    def __init__(self):
        # Map: roomId -> List[{ws: WebSocket, role: str}]
        self.active_connections: Dict[str, List[dict]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, role: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        if len(self.active_connections[room_id]) >= MAX_USERS_PER_ROOM:
            await websocket.close(code=4003, reason="Room is full")
            logger.warning(f"Connection rejected: Room {room_id} is full", extra={"error_code": ErrorCode.ROOM_FULL})
            raise WebSocketDisconnect
            
        self.active_connections[room_id].append({"ws": websocket, "role": role})
        metrics.increment_connections()
        logger.info(f"User connected", extra={"role": role})

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            # Remove by object identity
            initial_count = len(self.active_connections[room_id])
            self.active_connections[room_id] = [c for c in self.active_connections[room_id] if c["ws"] != websocket]
            
            if len(self.active_connections[room_id]) < initial_count:
                metrics.decrement_connections()
                logger.info(f"User disconnected")
            
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                if room_id in room_event_cache:
                    del room_event_cache[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            metrics.broadcasts_total += 1
            for connection in self.active_connections[room_id]:
                try:
                    await connection["ws"].send_json(message)
                except Exception as e:
                    metrics.track_broadcast_error()
                    logger.error(f"Broadcast failed to client", exc_info=True)
                    pass

manager = ConnectionManager()

# Background Keep-Alive Task
async def keep_alive_task():
    while True:
        await asyncio.sleep(KEEP_ALIVE_INTERVAL)
        for room_id, connections in list(manager.active_connections.items()):
            if not connections: 
                continue
            
            ping_msg = {"type": "ping", "payload": {"ts": int(time.time() * 1000)}}
            
            for conn in list(connections):
                try:
                    await conn["ws"].send_json(ping_msg)
                except Exception:
                    # Will be cleaned up by disconnect
                    pass

# Background Cleanup Task
CLEANUP_INTERVAL = 3600 # 1 hour
ROOM_TTL = 24 * 3600 * 1000 # 24 hours in milliseconds

async def cleanup_expired_rooms_task():
    while True:
        try:
            print("Running cleanup task...")
            current_time = get_current_timestamp()
            threshold = current_time - ROOM_TTL
            
            async with async_session() as session:
                # Find expired rooms
                statement = select(Room).where(Room.updatedAt < threshold)
                result = await session.execute(statement)
                expired_rooms = result.scalars().all()
                
                count = 0
                for room in expired_rooms:
                    # Optional: Check if room is currently active in memory?
                    # If active, maybe extend TTL? 
                    # For now, strict TTL based on DB update time.
                    # Active rooms update 'updatedAt' on every edit, so they are safe.
                    # Only idle rooms will be deleted.
                    
                    # Also need to close active WS connections if any (edge case)
                    if room.roomId in manager.active_connections:
                        for conn in manager.active_connections[room.roomId]:
                            await conn["ws"].close(code=4004, reason="Room expired")
                        del manager.active_connections[room.roomId]

                    await session.delete(room)
                    count += 1
                
                if count > 0:
                    await session.commit()
                    print(f"Cleaned up {count} expired rooms")
                    
        except Exception as e:
            print(f"Cleanup task error: {e}")
            
        await asyncio.sleep(CLEANUP_INTERVAL)

@app.on_event("startup")
async def startup_event():
    await init_db() 
    asyncio.create_task(keep_alive_task())
    asyncio.create_task(cleanup_expired_rooms_task())

def get_current_timestamp():
    return int(time.time() * 1000)

async def get_room_snapshot(session: AsyncSession, room_id: str) -> Optional[dict]:
    statement = select(Room).where(Room.roomId == room_id).options(selectinload(Room.items))
    result = await session.execute(statement)
    room = result.scalars().first()
    
    if not room:
        return None
    
    # Sort items: Incomplete first, then by creation time
    sorted_items = sorted(room.items, key=lambda x: (x.done, x.createdAt))

    return {
        "roomId": room.roomId,
        "roomName": room.roomName,
        "version": room.version,
        "createdAt": room.createdAt,
        "updatedAt": room.updatedAt,
        "joinToken": room.joinToken, # Send joinToken so members can share it
        "items": [item.model_dump() for item in sorted_items]
    }

# --- REST API for Room Creation ---

@app.post("/api/rooms")
async def create_room(room_data: RoomCreate, session: AsyncSession = Depends(get_db)):
    # Generate short ID if not provided (6 chars, safe for URL)
    new_room_id = room_data.roomId
    if not new_room_id:
        new_room_id = generate(size=6)
    
    with LogContext(action="create_room"):
        # Retry logic for collision (simple)
        for _ in range(3):
            try:
                start_time = time.time()
                room = Room(
                    roomId=new_room_id,
                    roomName=room_data.roomName,
                    # tokens are generated by default_factory in Model
                )
                session.add(room)
                await session.commit()
                await session.refresh(room)
                
                metrics.track_db_latency(start_time)
                logger.info(f"Room created", extra={"room_id": room.roomId})
                
                return {
                    "roomId": room.roomId,
                    "roomName": room.roomName,
                    "adminToken": room.adminToken,
                    "joinToken": room.joinToken
                }
            except IntegrityError:
                await session.rollback()
                if room_data.roomId: # If user provided specific ID and failed, error out
                    logger.warning("Room ID collision or duplicate", extra={"room_id": room_data.roomId})
                    metrics.track_error()
                    raise HTTPException(status_code=400, detail="Room ID already exists")
                new_room_id = generate(size=6) # Retry with new ID
        
        logger.error("Failed to generate unique Room ID after retries")
        metrics.track_error()
        raise HTTPException(status_code=500, detail="Failed to generate unique Room ID")

@app.post("/api/rooms/{room_id}/rotate-token")
async def rotate_token(
    room_id: str, 
    payload: dict, # Expect {"adminToken": "..."}
    session: AsyncSession = Depends(get_db)
):
    """
    Regenerates the joinToken for a room.
    Requires valid adminToken.
    """
    provided_token = payload.get("adminToken")
    if not provided_token:
        raise HTTPException(status_code=401, detail="Admin token required")

    statement = select(Room).where(Room.roomId == room_id)
    result = await session.execute(statement)
    room = result.scalars().first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    if room.adminToken != provided_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
        
    # Rotate Join Token
    old_token = room.joinToken
    # Note: Room model has default factory, but here we update manually
    from uuid import uuid4
    room.joinToken = str(uuid4())
    session.add(room)
    await session.commit()
    
    logger.info(f"Join token rotated", extra={"room_id": room_id})
    
    # Notify all connected clients (Admin & Members)
    # Members with old token will be effectively kicked on next reconnect/refresh
    # Ideally, we should also close their current WS connections, but for MVP
    # letting them stay until refresh is acceptable, OR we can force disconnect.
    
    # Let's broadcast an event so frontend can update its UI or warn user
    await manager.broadcast(room_id, {
        "type": "token_rotated",
        "payload": {
            "newJoinToken": room.joinToken
        }
    })
    
    return {"newJoinToken": room.joinToken}


# --- WebSocket ---

@app.websocket("/ws/{room_id}/{user_name}")
async def websocket_endpoint(
    websocket: WebSocket, 
    room_id: str, 
    user_name: str, 
    token: Optional[str] = Query(None)
):
    # Setup Context Logger
    conn_id = str(uuid4())
    
    # 1. Validate Room & Token BEFORE accepting
    with LogContext(room_id=room_id, user=user_name, conn_id=conn_id):
        async with async_session() as session:
            statement = select(Room).where(Room.roomId == room_id)
            result = await session.execute(statement)
            room = result.scalars().first()
            
            if not room:
                # Room does not exist. 
                # In Phase 4, we DO NOT auto-create rooms via WS anymore.
                # Must use REST API.
                logger.warning("Connection rejected: Room not found", extra={"error_code": ErrorCode.ROOM_NOT_FOUND})
                await websocket.close(code=4004, reason="Room not found. Please create one first.")
                return

            # Auth Check
            role = "guest"
            if token == room.adminToken:
                role = "admin"
            elif token == room.joinToken:
                role = "member"
            else:
                logger.warning("Connection rejected: Invalid token", extra={"error_code": ErrorCode.AUTH_INVALID_TOKEN})
                await websocket.close(code=4001, reason="Unauthorized: Invalid Token")
                return

        # 2. Connect
        try:
            await manager.connect(websocket, room_id, role)
        except WebSocketDisconnect:
            return

        # 3. Send Initial Snapshot
        # Re-fetch with items loaded
        read_start = time.time()
        async with async_session() as session:
            snapshot = await get_room_snapshot(session, room_id)
            metrics.track_db_latency(read_start, is_write=False)
            
            # If admin, we could include adminToken in payload, but usually not needed in snapshot
            # Frontend already has it from URL/LocalStorage
            await websocket.send_json({
                "type": "snapshot",
                "payload": snapshot,
                "role": role # Tell frontend its role
            })
            
        # Initialize Cache
        if room_id not in room_event_cache:
            room_event_cache[room_id] = deque(maxlen=EVENT_HISTORY_LIMIT)

        # 4. Event Loop
        try:
            while True:
                data = await websocket.receive_json()
                event_type, payload, client_event_id = parse_event_message(data)
                if not event_type or not payload:
                    continue
                
                metrics.track_event()

                # Idempotency Check
                if client_event_id and client_event_id in room_event_cache.get(room_id, []):
                    logger.info(f"Duplicate event ignored: {client_event_id}")
                    continue
                
                if event_type == "pong":
                    continue

                # --- Security: Rate Limiting ---
                # Key: roomId:userName (User level limiting)
                limit_key = f"{room_id}:{user_name}"
                if not rate_limiter.check_limit(limit_key):
                    logger.warning(f"Rate limit exceeded for {user_name}")
                    try:
                        await websocket.send_json({
                            "type": "error", 
                            "payload": {"message": "You are doing that too fast!"}
                        })
                    except Exception:
                         # Client likely disconnected, just stop processing
                         break
                    continue

                updated = False
                
                # Measure DB Transaction Time
                db_start = time.time()
                
                async with async_session() as session:
                    statement = select(Room).where(Room.roomId == room_id).options(selectinload(Room.items))
                    result = await session.execute(statement)
                    current_room = result.scalars().first()
                    
                    if not current_room: continue

                    # Permission Check Helper
                    is_admin = (role == "admin")
                    
                    # Log Context with Event ID
                    log_extra = {"event_id": client_event_id} if client_event_id else {}
                    
                    if event_type == "item_add":
                        # Member & Admin can add
                        if len(current_room.items) >= MAX_ITEMS_PER_ROOM:
                            await websocket.send_json({"type": "error", "payload": {"message": "Room limit reached"}})
                            logger.warning("Item limit reached", extra={**log_extra, "error_code": ErrorCode.ITEM_LIMIT_REACHED})
                            continue

                        raw_text = payload.get("text")
                        # --- Security: Sanitization ---
                        text = sanitize_text(raw_text)

                        # Priority validation
                        raw_priority = payload.get("priority")
                        try:
                            priority = validate_priority(raw_priority)
                        except ValueError as e:
                            try:
                                await websocket.send_json({"type": "error", "payload": {"message": str(e)}})
                            except Exception:
                                break
                            logger.warning("Invalid priority", extra={**log_extra, "priority": raw_priority})
                            continue

                        if text:
                            new_item = TodoItem(
                                text=text[:MAX_ITEM_LENGTH],
                                priority=priority,
                                room_db_id=current_room.id
                            )
                            session.add(new_item)
                            updated = True
                            logger.info("Item added", extra={**log_extra, "item_text_len": len(text), "priority": priority})

                    elif event_type == "item_toggle":
                        item_id = payload.get("itemId")
                        done = payload.get("done")
                        target = next((i for i in current_room.items if i.id == item_id), None)
                        if target and target.done != done:
                            target.done = done
                            target.doneBy = user_name if done else None
                            target.updatedAt = get_current_timestamp()
                            session.add(target)
                            updated = True
                            logger.info("Item toggled", extra={**log_extra, "item_id": item_id, "done": done})

                    elif event_type == "item_edit":
                        item_id = payload.get("itemId")
                        raw_text = payload.get("text")
                        raw_priority = payload.get("priority")

                        # Priority validation (optional field)
                        priority = None
                        if raw_priority is not None:
                            try:
                                priority = validate_priority(raw_priority)
                            except ValueError as e:
                                try:
                                    await websocket.send_json({"type": "error", "payload": {"message": str(e)}})
                                except Exception:
                                    break
                                logger.warning("Invalid priority", extra={**log_extra, "priority": raw_priority})
                                continue

                        target = next((i for i in current_room.items if i.id == item_id), None)
                        if target:
                            changed = apply_item_edit(
                                target=target,
                                raw_text=raw_text,
                                priority=priority,
                                updated_at=get_current_timestamp(),
                            )
                            if changed:
                                session.add(target)
                                updated = True
                            logger.info("Item edited", extra={**log_extra, "item_id": item_id, "has_priority": priority is not None})

                    elif event_type == "item_delete":
                        item_id = payload.get("itemId")
                        target = next((i for i in current_room.items if i.id == item_id), None)
                        if target:
                            await session.delete(target)
                            updated = True
                            logger.info("Item deleted", extra={**log_extra, "item_id": item_id})
                    
                    # --- Admin Only Actions ---
                    
                    elif event_type == "room_rename":
                        if not is_admin:
                            await websocket.send_json({"type": "error", "payload": {"message": "Admin only"}})
                            logger.warning("Unauthorized rename attempt", extra={**log_extra, "error_code": ErrorCode.AUTH_NO_PERMISSION})
                            continue
                        
                        raw_name = payload.get("roomName")
                        # --- Security: Sanitization ---
                        new_name = sanitize_text(raw_name)
                        
                        if new_name:
                            current_room.roomName = new_name[:50]
                            session.add(current_room)
                            updated = True
                            logger.info("Room renamed", extra={**log_extra, "new_name": new_name})

                    elif event_type == "room_clear_done":
                        if not is_admin:
                            await websocket.send_json({"type": "error", "payload": {"message": "Admin only"}})
                            continue
                        
                        # Delete completed items
                        count_deleted = 0
                        for item in current_room.items:
                            if item.done:
                                await session.delete(item)
                                count_deleted += 1
                        updated = True
                        logger.info("Room cleared", extra={**log_extra, "count": count_deleted})

                    # --- Commit & Broadcast ---

                    if updated:
                        current_room.version += 1
                        current_room.updatedAt = get_current_timestamp()
                        session.add(current_room)
                        
                        await session.commit()
                        await session.refresh(current_room) 
                        
                        # Record Latency
                        metrics.track_db_latency(db_start, is_write=True)
                        
                        if client_event_id:
                            if room_id not in room_event_cache:
                                room_event_cache[room_id] = deque(maxlen=EVENT_HISTORY_LIMIT)
                            room_event_cache[room_id].append(client_event_id)

                        snapshot = await get_room_snapshot(session, room_id)
                        await manager.broadcast(room_id, {
                            "type": "snapshot",
                            "payload": snapshot
                        })

        except WebSocketDisconnect:
            with LogContext(room_id=room_id, user=user_name, conn_id=conn_id):
                 manager.disconnect(websocket, room_id)
        except Exception as e:
            with LogContext(room_id=room_id, user=user_name, conn_id=conn_id):
                logger.error(f"Unexpected error: {e}", exc_info=True)
                metrics.track_error()
                manager.disconnect(websocket, room_id)
