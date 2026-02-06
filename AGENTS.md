# ShareList (Room Todo) 项目上下文

## 项目概览

**ShareList** 是一个实时多人协同清单应用，主打“即开即用”的极简体验。用户无需登录，创建一个“房间”后，即可通过分享链接或房间码邀请朋友加入，实现在多台设备上实时同步待办事项（新增、勾选、编辑、删除）。

项目采用 **Monorepo (单体仓库)** 结构，包含 Next.js 前端和 FastAPI 后端。

## 技术栈

*   **前端 (Frontend):** Next.js 16 (App Router), TypeScript, Tailwind CSS, Shadcn/ui。
*   **后端 (Backend):** Python 3.8+, FastAPI, WebSockets, Pydantic。
*   **数据存储:** 内存存储 (MVP 阶段)，为未来接入数据库预留了接口。
*   **实时通信:** 原生 WebSockets，配合自定义 JSON 事件协议。

## 架构与核心概念

### Monorepo 目录结构
*   `frontend/`: 存放 Next.js 前端应用代码。
*   `backend/`: 存放 Python FastAPI 后端服务代码。
*   `package.json` (根目录): 项目编排脚本，用于统一启动和安装依赖。

### 实时协同机制
*   **通信模式:** 客户端与服务端通过 WebSocket 全双工通信。
*   **状态管理:** 服务端作为“单一真相源 (Single Source of Truth)”，维护 `RoomState`。
*   **快照策略 (Snapshot):** 连接建立或状态变更后，服务端会向所有客户端广播完整的房间状态快照。
*   **系统加固 (System Hardening):**
    *   **幂等性 (Idempotency):** 客户端所有写操作均携带 `clientEventId` (UUID)。服务端记录已处理的事件 ID，防止因网络重试导致的重复操作。
    *   **版本控制:** 房间状态包含 `version` 字段，确保时序正确。
    *   **安全限制:** 限制单房间人数 (50)、事项数量 (200) 及文本长度 (500) 以防止资源滥用。
    *   **心跳保活:** 服务端定期发送 `ping`，客户端回复 `pong`，以此维护连接健康。

## 构建与运行

### 前置要求
*   Node.js v18+
*   Python v3.8+
*   `npm` 或 `yarn`

### 常用命令 (根目录)

| 命令 | 说明 |
| :--- | :--- |
| `npm run install:all` | 一键安装所有依赖（前端 npm + 后端 pip）。 |
| `npm run dev` | 并行启动前端 (localhost:3000) 和后端 (localhost:8000)。 |
| `npm run dev --prefix frontend` | 单独启动前端。 |
| `uvicorn backend.main:app --reload` | 单独启动后端。 |

### 配置说明
环境变量通过 `frontend/.env.local` 文件配置。

*   `NEXT_PUBLIC_WS_URL`: WebSocket 服务地址 (默认为 `ws://localhost:8000`)。
    *   **提示:** 在局域网真机测试时，请将其修改为本机的 IP 地址 (例如 `ws://192.168.1.5:8000`)。

## 关键目录说明

*   **`backend/`**:
    *   `main.py`: 后端核心文件，包含 FastAPI 应用入口、WebSocket 端点、内存存储逻辑及连接管理。
    *   `requirements.txt`: Python 依赖列表。
*   **`frontend/`**:
    *   `src/app/room/[roomId]/page.tsx`: 核心房间页面，负责处理 WebSocket 连接、状态同步及 UI 渲染。
    *   `src/lib/store.ts`: (遗留/备份) 本地存储工具函数。
*   **`docs/`**:
    *   `EVENT_PROTOCOL.md`: 前后端通信协议规范 (Add, Toggle, Edit, Delete, Snapshot, Ping/Pong)。
    *   `STARTUP_GUIDE.md`: 项目启动与环境配置指南。
    *   `QA_CHECKLIST.md`: 手工验收测试用例。

## 开发规范

*   **协议先行:** 新增功能时，必须先在 `docs/EVENT_PROTOCOL.md` 中定义数据交换格式。
*   **幂等性原则:** 客户端发起任何修改状态的请求，**必须**生成并携带 `clientEventId`。
*   **防御性编程:** 后端必须对房间大小、并发数进行限制，防止服务崩溃。
*   **样式规范:** 遵循现有的 Tailwind CSS 和 Shadcn/ui 设计风格。
*   **日志记录:** 完成阶段性功能、修复 Bug 或新功能开发后，**必须**更新 `log.md` 文件。
