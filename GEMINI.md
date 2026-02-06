# ShareList (Room Todo) 项目上下文

## 项目概览

**ShareList** 是一个实时多人协同清单应用，主打“即开即用”的极简体验。用户无需登录，创建一个“房间”后，即可通过分享链接或房间码邀请朋友加入，实现在多台设备上实时同步待办事项（新增、勾选、编辑、删除）。

项目采用 **Monorepo (单体仓库)** 结构，包含 Next.js 前端和 FastAPI 后端，并支持 Docker 容器化部署。

## 技术栈

*   **前端 (Frontend):** Next.js 16 (App Router), TypeScript, Tailwind CSS, Shadcn/ui。
*   **后端 (Backend):** Python 3.11, FastAPI, WebSockets, SQLModel (SQLAlchemy + Pydantic)。
*   **数据存储:** Supabase PostgreSQL (via `asyncpg` driver & Session Pooler)。
*   **实时通信:** 原生 WebSockets，配合自定义 JSON 事件协议。
*   **部署:** Docker, Docker Compose。

## 架构与核心概念

### Monorepo 目录结构
*   `frontend/`: 存放 Next.js 前端应用代码。
*   `backend/`: 存放 Python FastAPI 后端服务代码。
*   `package.json` (根目录): 项目编排脚本，用于统一启动和安装依赖。
*   `docker-compose.yml`: 容器编排文件。

### 权限与安全 (Minimalist Auth)
*   **无账号体系**: 不依赖传统的 User/Pass 或 OAuth。
*   **Token 鉴权**:
    *   **Admin Token**: 创建房间时生成，拥有最高权限（改名、清空、踢人等）。
    *   **Join Token**: 仅拥有普通成员权限（增删改查清单项）。
*   **访问控制**: 
    *   WebSocket 连接必须携带有效 Token。
    *   无 Token 访问房间页会显示 `RoomGate` 组件，要求输入邀请码。
*   **系统加固**:
    *   **幂等性**: 客户端写操作携带 `clientEventId`，后端防重放。
    *   **过期清理**: 后台任务自动清理超过 24 小时未活动的房间。
    *   **连接限制**: 单房间限 50 人，防止资源耗尽。

## 构建与运行

### 前置要求
*   Node.js v18+
*   Python v3.9+
*   `npm` 或 `yarn`
*   (可选) Docker & Docker Compose

### 常用命令 (根目录)

| 命令 | 说明 |
| :--- | :--- |
| `npm run install:all` | 一键安装所有依赖（前端 npm + 后端 pip）。 |
| `npm run dev` | 并行启动前端 (localhost:3000) 和后端 (localhost:8000)。 |
| `docker-compose up --build` | 使用 Docker 一键构建并启动整个服务栈。 |

### 环境变量配置
*   **前端**: `frontend/.env.local`
    *   `NEXT_PUBLIC_WS_URL`: WebSocket 地址 (本地开发通常为 `ws://localhost:8000`)。
*   **后端**: `backend/.env`
    *   `DATABASE_URL`: Postgres 连接字符串 (推荐使用 Supabase Session Pooler 端口 5432)。

## 关键文件说明

*   **`backend/`**:
    *   `main.py`: 核心入口，包含 HTTP API (`/api/rooms`)、WebSocket 鉴权与事件循环、定时清理任务。
    *   `models.py`: SQLModel 数据库模型定义 (`Room`, `TodoItem`)。
    *   `database.py`: 异步数据库连接与 Session 管理。
*   **`frontend/`**:
    *   `src/app/room/[roomId]/page.tsx`: 核心房间页，包含 WS 连接管理、状态机 (Gate/Error/Loading/Connected)。
    *   `src/components/RoomGate.tsx`: 门禁组件，处理 Token 输入。
    *   `src/components/RoomError.tsx`: 错误提示组件 (404/401)。

## 开发规范

*   **协议先行:** 新增功能时，必须先在 `docs/EVENT_PROTOCOL.md` 中定义数据交换格式。
*   **数据库迁移:** 修改 `models.py` 后，目前采用 Drop & Re-create 策略 (MVP阶段)，需手动清理旧表。
*   **权限意识:** 任何破坏性操作（如清空、删除房间）必须检查 `role == 'admin'`。
*   **样式规范:** 遵循现有的 Tailwind CSS 和 Shadcn/ui 设计风格。
*   **日志记录:** 完成阶段性功能、修复 Bug 或新功能开发后，**必须**更新 `log.md` 文件。
