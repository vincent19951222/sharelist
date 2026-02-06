# Event Protocol

This document defines the WebSocket communication protocol between the Client (Next.js) and Server (FastAPI).

## Connection
**URL:** `ws://<host>:8000/ws/{roomId}/{userName}?token=<invite-or-admin-token>`
**Note:** Token is required for all connections. `roomId` alone does not grant access.

## Data Models

### RoomState
```json
{
  "roomId": "string",
  "roomName": "string",
  "version": number, // Incremental version number
  "createdAt": number,
  "updatedAt": number,
  "joinToken": "string", // Invite token for sharing
  "items": [TodoItem]
}
```

### TodoItem
```json
{
  "id": "string",
  "text": "string",
  "done": boolean,
  "doneBy": "string | null",
  "priority": "high" | "medium" | "low",
  "createdAt": number,
  "updatedAt": number
}
```

## Client -> Server Events

The client sends JSON objects with a `type` and `payload`. **All state-modifying payloads must include a `clientEventId`.**

### 1. Add Item
```json
{
  "type": "item_add",
  "payload": {
    "clientEventId": "unique-id-string",
    "text": "Buy milk",
    "priority": "high"
  }
}
```
Note: `priority` is optional and defaults to "medium". Valid values: "high", "medium", "low".

### 2. Toggle Item
```json
{
  "type": "item_toggle",
  "payload": {
    "clientEventId": "unique-id-string",
    "itemId": "uuid-string",
    "done": true
  }
}
```

### 3. Edit Item
```json
{
  "type": "item_edit",
  "payload": {
    "clientEventId": "unique-id-string",
    "itemId": "uuid-string",
    "text": "Buy almond milk",
    "priority": "low"
  }
}
```
Note: Both `text` and `priority` are optional. At least one must be provided.

### 4. Delete Item
```json
{
  "type": "item_delete",
  "payload": {
    "clientEventId": "unique-id-string",
    "itemId": "uuid-string"
  }
}
```

### 5. Rename Room (Admin Only)
```json
{
  "type": "room_rename",
  "payload": {
    "clientEventId": "unique-id-string",
    "roomName": "New Room Name"
  }
}
```

### 6. Clear Completed Items (Admin Only)
```json
{
  "type": "room_clear_done",
  "payload": {
    "clientEventId": "unique-id-string"
  }
}
```

### 7. Pong (Heartbeat)
```json
{
  "type": "pong",
  "payload": {}
}
```

## Server -> Client Events

### 1. Snapshot
Sent immediately upon connection and after any state change.
```json
{
  "type": "snapshot",
  "payload": <RoomState Object>,
  "role": "admin | member"
}
```

### 2. Ping (Heartbeat)
Sent periodically by server to keep connection alive.
```json
{
  "type": "ping",
  "payload": { "ts": 1234567890 }
}
```

### 3. Error
Sent when an action is rejected (e.g. room full).
```json
{
  "type": "error",
  "payload": {
    "message": "Room is full (max items reached)."
  }
}
```

### 4. Token Rotated
Sent to all clients when the invite token is reset by an Admin.
```json
{
  "type": "token_rotated",
  "payload": {
    "newJoinToken": "string"
  }
}
```

## Close Codes (WebSocket)

- `4001`: Unauthorized / invalid token
- `4003`: Room full
- `4004`: Room not found or expired
