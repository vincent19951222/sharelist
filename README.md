# ShareList

ShareList 当前是一个 **固定房间 Quest 面板**：前端 4 个页面，后端 FastAPI + WebSocket 实时同步，数据库保存房间、成员、任务、自动任务和积分流水。

第一版只开放一个 seed 房间：
- `roomId = 9999`
- 允许进入的名字：`vincent`、`cindy`

## Features

- 固定房间登录：入口页用 `roomId + name` 校验进入，不再支持创建房间、分享邀请或 Recent Rooms。
- 实时任务面板：房间页支持新增、编辑、勾选、删除 Quest，所有写操作通过 WebSocket 同步。
- Auto Quests：可配置重复星期、奖励 GP、启用开关；用户进入房间时按上海时区懒生成当天任务。
- GP 积分：任务完成时记账，取消完成时回滚；Profile 页展示总分、周/月统计和有效流水。
- Presence：房间页返回成员头像和在线状态。

## Stack

- Frontend: Next.js 16, TypeScript, Tailwind CSS
- Backend: FastAPI, WebSockets, SQLModel
- Database:
  - Local development: SQLite (`sqlite+aiosqlite`)
  - Remote deployment: PostgreSQL / Supabase (`postgresql+asyncpg`)

## Local Development

1. 安装依赖

```bash
npm run install:all
```

2. 准备环境变量

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. 启动前后端

```bash
npm run dev
```

默认开发模式会监听局域网地址，且前端在未配置 `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL` 时，会自动使用当前访问主机的 `:8000` 作为后端地址。

- Frontend: [http://localhost:3333](http://localhost:3333)
- Backend: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

同一局域网设备可直接访问：

- `http://<你的局域网IP>:3333`

## Test Commands

后端单测：

```bash
backend/.venv/bin/python -m pytest backend/tests/test_event_handling.py backend/tests/test_priority.py
```

前端生产构建：

```bash
npm run build --prefix frontend
```

## Runtime Model

- `POST /api/rooms/access`
  - 用 `roomId + name` 校验访问权限，并返回当前用户资料。
- `GET /api/rooms/{roomId}/snapshot?name=<userName>`
  - 返回房间首屏快照；前端会先用它完成初始加载，再接入 WebSocket 实时同步。
- `GET /api/rooms/{roomId}/profiles/{userId}`
  - 返回 Profile 总分、周/月统计和历史流水。
- `ws://<host>:8000/ws/{roomId}/{userName}`
  - 连接后推送包含 `room/currentUser/members/items/autoQuests` 的快照。

## Notes

- seed 房间 `9999` 设置为 `never_expires=true`，不会参与 24 小时过期清理。
- 旧的 `adminToken / joinToken / rotate invite / priority filter` 已从运行时产品流程移除；旧字段仅作为历史兼容遗留。

## Docs

- [Event Protocol](./docs/EVENT_PROTOCOL.md)
- [Startup Guide](./docs/STARTUP_GUIDE.md)
- [QA Checklist](./docs/QA_CHECKLIST.md)
- [Development Log](./log.md)
