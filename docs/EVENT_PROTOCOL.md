# Event Protocol

本文件定义当前 ShareList V1 固定房间版本的实时同步协议。

## HTTP Bootstrap

房间页在建立 WebSocket 之前，会先通过 HTTP 拉取一次首屏快照，避免 WebSocket 首帧未及时到达时页面无限 loading。

**URL**

```text
GET /api/rooms/{roomId}/snapshot?name={userName}
```

返回体与下文 `snapshot.payload` 一致。

## Connection

**URL**

```text
ws://<host>:8000/ws/{roomId}/{userName}
```

**鉴权规则**

- 不再使用 `token`
- 服务端根据 `room_members` 校验 `roomId + userName`
- 当前 seed 仅允许：
  - `roomId = 9999`
  - `userName = vincent | cindy`

## Snapshot Shape

连接建立成功后，以及每次状态变更后，服务端向客户端发送 `snapshot`：

```json
{
  "type": "snapshot",
  "payload": {
    "room": {
      "roomId": "9999",
      "title": "我的房间",
      "timezone": "Asia/Shanghai"
    },
    "currentUser": {
      "userId": "string",
      "name": "vincent",
      "displayName": "Vincent",
      "avatarUrl": "https://...",
      "role": "admin",
      "isOnline": true
    },
    "members": [Member],
    "items": [TodoItem],
    "autoQuests": [AutoQuest]
  }
}
```

### Member

```json
{
  "userId": "string",
  "name": "vincent",
  "displayName": "Vincent",
  "avatarUrl": "https://...",
  "role": "admin",
  "isOnline": true
}
```

### TodoItem

```json
{
  "id": "string",
  "title": "Buy almond milk",
  "done": false,
  "rewardGp": 10,
  "sourceType": "manual",
  "autoQuestId": null,
  "scheduledDate": null,
  "createdBy": "vincent",
  "completedBy": null,
  "completedAt": null,
  "createdAt": 1774186661311,
  "updatedAt": 1774186661311
}
```

说明：

- `sourceType = manual | auto_quest`
- `scheduledDate` 仅自动任务实例使用，格式 `YYYY-MM-DD`
- `items` 只返回“当前可见任务”：
  - 手动任务
  - 当天的自动任务实例
  - 不返回软删除任务

### AutoQuest

```json
{
  "id": "string",
  "title": "Laundry Day",
  "rewardGp": 10,
  "repeatDays": ["Wed", "Fri"],
  "isEnabled": true,
  "createdBy": "cindy",
  "createdAt": 1774186661311,
  "updatedAt": 1774186661311
}
```

## Client -> Server Events

所有写事件必须在 `payload` 中携带 `clientEventId`。

### `item_add`

```json
{
  "type": "item_add",
  "payload": {
    "clientEventId": "evt-1",
    "title": "Water plants",
    "rewardGp": 20
  }
}
```

### `item_edit`

```json
{
  "type": "item_edit",
  "payload": {
    "clientEventId": "evt-2",
    "itemId": "todo-id",
    "title": "Water the plants",
    "rewardGp": 30
  }
}
```

### `item_toggle`

```json
{
  "type": "item_toggle",
  "payload": {
    "clientEventId": "evt-3",
    "itemId": "todo-id",
    "done": true
  }
}
```

完成时会记一笔 GP 流水；取消完成时会把当前有效流水标记回滚。

### `item_delete`

```json
{
  "type": "item_delete",
  "payload": {
    "clientEventId": "evt-4",
    "itemId": "todo-id"
  }
}
```

删除采用软删除，避免 Auto Quest 的当天实例被重复生成。

### `auto_quest_create`

```json
{
  "type": "auto_quest_create",
  "payload": {
    "clientEventId": "evt-5",
    "title": "Laundry Day",
    "rewardGp": 10,
    "repeatDays": ["Wed", "Sat"]
  }
}
```

### `auto_quest_update`

```json
{
  "type": "auto_quest_update",
  "payload": {
    "clientEventId": "evt-6",
    "autoQuestId": "auto-id",
    "title": "Laundry Day",
    "rewardGp": 20,
    "repeatDays": ["Wed", "Fri"],
    "isEnabled": true
  }
}
```

### `auto_quest_toggle`

```json
{
  "type": "auto_quest_toggle",
  "payload": {
    "clientEventId": "evt-7",
    "autoQuestId": "auto-id",
    "isEnabled": false
  }
}
```

### `pong`

```json
{
  "type": "pong",
  "payload": {}
}
```

## Server -> Client Events

### `snapshot`

见上文 Snapshot Shape。

### `ping`

```json
{
  "type": "ping",
  "payload": {
    "ts": 1774186661311
  }
}
```

### `error`

```json
{
  "type": "error",
  "payload": {
    "message": "Quest name is required."
  }
}
```

## Profile API

### `GET /api/rooms/{roomId}/profiles/{userId}`

返回：

```json
{
  "userId": "string",
  "name": "vincent",
  "displayName": "Vincent",
  "avatarUrl": "https://...",
  "rank": "B",
  "totalGp": 240,
  "thisWeekGp": 40,
  "thisWeekCount": 2,
  "thisMonthGp": 120,
  "thisMonthCount": 6,
  "history": [
    {
      "id": "ledger-id",
      "todoItemId": "todo-id",
      "todoTitle": "Buy almond milk",
      "gpDelta": 10,
      "awardedAt": 1774186661311
    }
  ]
}
```

## Close Codes

- `4001`: Unauthorized
- `4003`: Room full
- `4004`: Room not found
