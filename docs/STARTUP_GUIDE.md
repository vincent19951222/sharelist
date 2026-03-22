# 启动与环境变量说明

本文档面向当前 ShareList V1 固定房间版本。

## 1. 环境要求

- Node.js 18+
- Python 3.11+
- npm

## 2. 本地快速启动

```bash
# 1. 安装根目录、前端和后端依赖
npm run install:all

# 2. 准备环境变量
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 3. 启动前后端
npm run dev
```

房间页首屏会先通过 HTTP 拉取一次 snapshot，再切到 WebSocket 实时同步；即使 WebSocket 首帧失败，也不会一直卡在 loading。

默认地址：

- Frontend: [http://localhost:3333](http://localhost:3333)
- Backend: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

## 3. 环境变量

### 后端 `backend/.env`

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./sharelist.db` | 本地默认 SQLite |
| `CORS_ALLOW_ORIGINS` | `*` | 本地开发默认放开，便于局域网访问；生产环境建议显式配置 |

本地示例：

```env
DATABASE_URL=sqlite+aiosqlite:///./sharelist.db
CORS_ALLOW_ORIGINS=*
```

远端 PostgreSQL / Supabase 示例：

```env
DATABASE_URL=postgresql+asyncpg://postgres.<project-ref>:<password>@<pooler-host>:5432/postgres
```

### 前端 `frontend/.env.local`

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | 留空时自动推导 | REST API 地址；默认跟随当前访问主机并使用 `:8000` |
| `NEXT_PUBLIC_WS_URL` | 留空时自动推导 | WebSocket 地址；默认跟随当前访问主机并使用 `:8000` |

示例：

如果本地开发前后端运行在同一台机器上，可以留空，不配置这两个变量。

如需手动覆盖：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 4. 当前运行时默认数据

应用启动时会自动 seed 出固定数据：

- 房间：`9999`
- 标题：`我的房间`
- 时区：`Asia/Shanghai`
- 可登录用户：`vincent`、`cindy`

当前版本不支持：

- 新建房间
- 邀请链接 / token
- Recent Rooms

## 5. 数据库策略

- 本地开发默认使用 SQLite，零外部依赖。
- 远端部署仍可切换 PostgreSQL / Supabase。
- 当前版本的表结构以 `rooms / users / room_members / todo_items / auto_quests / gp_ledger` 为主。
- 老的 token 房间表如果仍在历史 SQLite 文件中，不再参与运行时逻辑。

## 6. 局域网真机测试

如果手机要访问你电脑上的开发环境：

1. 获取电脑局域网 IP，例如 `192.168.1.5`
2. 直接运行 `npm run dev`
3. 手机访问 `http://192.168.1.5:3333`

只有在“前端和后端不在同一台机器”或者“需要强制指定后端地址”时，才需要手动设置：

```env
NEXT_PUBLIC_API_URL=http://192.168.1.5:8000
NEXT_PUBLIC_WS_URL=ws://192.168.1.5:8000
```

## 7. 常用命令

```bash
npm run dev
npm run build --prefix frontend
backend/.venv/bin/python -m pytest backend/tests/test_event_handling.py backend/tests/test_priority.py
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
