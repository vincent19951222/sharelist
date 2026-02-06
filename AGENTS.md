# ShareList (Room Todo) 项目上下文

## 项目概览

**ShareList** 是一个实时多人协同清单应用，主打“即开即用”的极简体验。用户无需登录，创建房间后可通过**邀请链接或邀请码（token）**加入，多端实时同步待办事项（新增、勾选、编辑、删除）。

当前项目已从 MVP 演进为 **Monorepo 全栈应用**（Next.js + FastAPI + PostgreSQL），具备基础权限控制、可靠性与可观测性。

## 技术栈

* **前端 (Frontend):** Next.js 16 (App Router), TypeScript, Tailwind CSS, Shadcn/ui。
* **后端 (Backend):** Python 3.11, FastAPI, WebSockets, SQLModel。
* **数据存储:** PostgreSQL（异步驱动 `asyncpg`，通过 `DATABASE_URL` 配置）。
* **实时通信:** 原生 WebSockets + 自定义 JSON 事件协议。
* **数据清理:** 房间 24h 无活动自动清理（后台定时任务）。

## 架构与核心概念

### Monorepo 目录结构
* `frontend/`: Next.js 前端应用。
* `backend/`: FastAPI 后端服务（API + WebSocket + DB 访问）。
* `docs/`: 协议、启动、测试与上线文档。
* `package.json` (根目录): 统一安装、启动与测试脚本。

### 实时协同机制
* **单一真相源:** 服务端数据库状态为准。
* **快照同步:** 连接建立与状态变更后，服务端广播 `snapshot`。
* **幂等性:** 写操作需携带 `clientEventId`，服务端做事件去重。
* **心跳保活:** 服务端发送 `ping`，客户端回 `pong`。
* **权限模型:**
  * `admin`: 创建者（可重命名、清理已完成、重置邀请）。
  * `member`: 通过邀请加入（可编辑事项）。
  * `guest`: 未授权，不可进入房间。

### 系统加固
* 房间人数上限（50）、事项上限（200）、文本长度上限（500）。
* 输入清洗（`bleach`）防止 XSS。
* 基础限流（按 `roomId:userName`）。
* 指标统计与系统观测端点：`GET /sys/stats`。

## 构建与运行

### 前置要求
* Node.js v18+
* Python v3.11+
* npm

### 环境变量

#### 后端：`backend/.env`
* `DATABASE_URL`：必填，未配置时后端启动会失败。

#### 前端：`frontend/.env.local`
* `NEXT_PUBLIC_WS_URL`：WebSocket 地址，默认 `ws://localhost:8000`
* `NEXT_PUBLIC_API_URL`：REST API 地址，默认 `http://localhost:8000`

> 局域网真机测试时请改为本机 IP（例如 `ws://192.168.1.5:8000`）。

### 常用命令（根目录）

| 命令 | 说明 |
| :--- | :--- |
| `npm run install:all` | 安装根目录 + 前端 npm 依赖，并安装后端 Python 依赖。 |
| `npm run dev` | 并行启动前端（3000）和后端（8000）。 |
| `npm run dev --prefix frontend` | 单独启动前端。 |
| `uvicorn backend.main:app --reload --port 8000` | 单独启动后端。 |
| `pytest backend/tests/test_priority.py` | 后端单元测试。 |
| `pytest tests/test_e2e.py` | 端到端测试（需本地服务已启动）。 |
| `python tests/load_test.py` | 简易并发压测脚本。 |

## 关键目录说明

* **`backend/`**
  * `main.py`: API/WebSocket 入口、连接管理、事件处理、定时任务。
  * `models.py`: `Room` / `TodoItem` 数据模型。
  * `database.py`: 异步数据库引擎与 Session。
  * `security.py`: 文本清洗与限流。
  * `logger.py` / `telemetry.py`: 结构化日志与指标。
* **`frontend/`**
  * `src/app/page.tsx`: 首页（创建房间、加入房间、最近房间）。
  * `src/app/room/[roomId]/page.tsx`: 房间核心页（WebSocket、状态同步、权限 UI）。
  * `src/lib/api.ts`: 与后端 REST API 交互。
  * `src/lib/store.ts`: 本地用户信息与最近房间缓存。
* **`docs/`**
  * `EVENT_PROTOCOL.md`: 前后端事件协议。
  * `STARTUP_GUIDE.md`: 启动与环境配置。
  * `QA_CHECKLIST.md`: 手工验收清单。
  * `LAUNCH_READINESS.md` / `LAUNCH_NEXT_STEPS.md`: 上线准备与后续路线。

## 开发规范

* **协议先行:** 新增事件/字段前，先更新 `docs/EVENT_PROTOCOL.md`。
* **幂等性原则:** 所有状态写操作必须包含 `clientEventId`。
* **权限清晰:** Admin-only 能力要在前端禁用态 + 后端强校验双保险。
* **防御性编程:** 后端必须维持容量限制、输入校验、异常兜底。
* **文档一致性:** 实现变更后同步更新 `README.md`、`docs/` 与本文件。
* **日志记录:** 阶段性功能或修复完成后更新 `log.md`。

## 常见风险点（开发时重点自检）

* WebSocket 异常分支是否会导致无限重连或重复连接。
* 事件 payload 缺失时是否会触发未捕获异常。
* snapshot 字段变更后，前端类型与协议文档是否同步。
* token 轮换后旧链接、Recent Rooms、RoomGate 的体验是否一致。
