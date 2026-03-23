# ShareList 项目上下文

## 项目概览

**ShareList** 当前是一个固定房间的 Room Quest 应用，不再是“即时建房 + 邀请加入”的协作清单。

第一版产品约束：

- 固定房间：`9999`
- 固定成员：`vincent`、`cindy`
- 访问方式：入口页输入 `roomId + name`
- 页面范围：
  - `entry`
  - `room`
  - `auto quests`
  - `profile`

## 技术栈

- Frontend: Next.js 16, TypeScript, Tailwind CSS
- Backend: FastAPI, WebSockets, SQLModel
- Database:
  - Local: SQLite (`sqlite+aiosqlite`)
  - Remote: PostgreSQL / Supabase (`postgresql+asyncpg`)

## 核心业务概念

### 访问控制

- 不再使用 `adminToken / joinToken`
- WebSocket 和 REST 都基于 `room_members` 校验访问关系
- 当前 seed 用户都属于同一房间，角色都是 `admin`

### 实时快照

服务端 `snapshot` 返回：

- `room`
- `currentUser`
- `members`
- `items`
- `autoQuests`

### Quest 体系

- `manual quest`
  - 房间页手动新增
- `auto quest`
  - 配置重复星期
  - 用户进入房间时按上海时区懒生成当天实例

### GP 积分

- 每个任务都带 `reward_gp`
- 完成任务：
  - 写 `completed_by_user_id`
  - 新增或激活一条 `gp_ledger`
- 取消完成：
  - 清空完成人和完成时间
  - 当前有效流水写 `reversed_at`
- Profile 页展示：
  - `totalGp`
  - `thisWeekGp`
  - `thisMonthGp`
  - `history`
  - `rank`

### Rank 规则

- `C`: `0+`
- `B`: `200+`
- `A`: `600+`
- `S`: `1200+`

## 数据模型

当前运行时核心表：

- `rooms`
  - `room_code`
  - `title`
  - `timezone`
  - `is_seeded`
  - `never_expires`
- `users`
  - `name`
  - `display_name`
  - `avatar_url`
- `room_members`
  - `room_id`
  - `user_id`
  - `role`
- `todo_items`
  - `title`
  - `reward_gp`
  - `source_type`
  - `auto_quest_id`
  - `scheduled_date`
  - `created_by_user_id`
  - `completed_by_user_id`
  - `completed_at`
  - `is_deleted`
- `auto_quests`
  - `title`
  - `reward_gp`
  - `repeat_mask`
  - `is_enabled`
  - `created_by_user_id`
- `gp_ledger`
  - `todo_item_id`
  - `todo_title`
  - `gp_delta`
  - `awarded_at`
  - `reversed_at`

## 运行与启动

### 环境变量

后端 `backend/.env`

- `DATABASE_URL`
- `CORS_ALLOW_ORIGINS`

前端 `frontend/.env.local`

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_WS_URL`

### 常用命令

| 命令 | 说明 |
| --- | --- |
| `npm run install:all` | 安装根目录、前端和后端依赖 |
| `npm run dev` | 前端 `3333` + 后端 `8000` |
| `npm run build --prefix frontend` | 前端生产构建 |
| `backend/.venv/bin/python -m pytest backend/tests/test_event_handling.py backend/tests/test_priority.py` | 后端单测 |
| `uvicorn backend.main:app --reload --port 8000` | 单独启动后端 |

## 开发规范

- 协议变更先更新 `docs/EVENT_PROTOCOL.md`
- 所有写事件必须带 `clientEventId`
- 自动任务相关改动要同时检查：
  - 当天懒生成是否重复
  - 删除当天实例后是否被重新生成
  - 取消完成是否正确回滚 GP
- 文档同步：
  - `README.md`
  - `docs/STARTUP_GUIDE.md`
  - `docs/EVENT_PROTOCOL.md`
  - `log.md`
- 阶段性完成后更新 `log.md`

## 风险点

- WebSocket 断线重连后是否重复连接
- `snapshot` 字段变化后前端类型是否同步
- Auto Quest 更新后当天实例是否需要同步刷新
- 软删除是否阻止当天自动任务重复生成
- GP 流水是否和任务完成/撤销严格对应
