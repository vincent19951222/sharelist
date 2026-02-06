# 开发日志 (Development Log)

记录 ShareList 项目从零开始的开发全过程。

## Phase 1: 项目初始化与 MVP 前端 (Local-Only)
**时间**: 2026-02-04
**目标**: 快速搭建 Next.js 项目骨架，实现核心清单功能，验证 UI/UX。

### 核心产出
*   **工程搭建**: 使用 `Next.js 16 (App Router)` + `TypeScript` + `Tailwind CSS` + `Shadcn/ui` 初始化项目。
*   **本地存储**: 实现基于 `localStorage` 的数据持久化，确保刷新页面不丢数据。
*   **核心功能**:
    *   **房间管理**: 首页输入昵称创建房间，生成短链 Room ID。
    *   **清单操作**: 实现了新增、删除、勾选完成、编辑文本。
    *   **视图优化**: 支持“隐藏已完成”事项，显示完成进度。
*   **分享体验**:
    *   集成 `navigator.share` (Web Share API) 实现原生系统分享。
    *   实现复制链接和 Room ID 的兜底逻辑。

---

## Phase 2: 后端服务与实时协同 (Real-time Collaboration)
**时间**: 2026-02-04
**目标**: 引入后端服务，实现多端数据实时同步，支持多人协作。

### 核心产出
*   **后端架构**:
    *   引入 `Python FastAPI` + `WebSockets`。
    *   设计了基于内存 (`In-Memory`) 的房间状态存储。
*   **WebSocket 协议**:
    *   定义了 `item_add`, `item_toggle`, `item_edit`, `item_delete` 等事件。
    *   实现了 `snapshot` 机制：连接建立后立即下发全量状态。
*   **前端改造**:
    *   移除 LocalStorage 逻辑，全面对接 WebSocket 事件。
    *   增加连接状态指示器 (WiFi 图标：💚 已连接 / 🔴 断开)。
*   **交付保障**:
    *   产出 `EVENT_PROTOCOL.md` (通信协议文档)。
    *   产出 `MANUAL_TEST.md` (手工验收 Checklist)。
    *   配置 `concurrently` 实现 `npm run dev:all` 一键启动前后端。

---

## Phase 2.1: 工程重构 (Monorepo Refactoring)
**时间**: 2026-02-05
**目标**: 规范项目结构，分离前后端代码，符合最佳实践。

### 核心产出
*   **目录重组**:
    *   创建 `frontend/` 目录，迁移 Next.js 相关代码。
    *   保留 `backend/` 目录。
    *   根目录仅保留编排脚本和文档。
*   **脚本优化**: 更新根目录 `package.json`，支持 `npm run install:all` 和 `npm run dev` 统一管理子项目。
*   **文档更新**: 全面更新 `README.md` 和 `docs/STARTUP_GUIDE.md` 以适配新结构。

---

## Phase 2.5: 系统加固 (System Hardening)
**时间**: 2026-02-05
**目标**: 提升系统健壮性，解决网络抖动、并发冲突和资源滥用问题。

### 核心产出
*   **一致性与幂等性**:
    *   引入 `clientEventId` (UUID)，前端每次写操作带上 ID。
    *   后端实现 `Idempotency Check` (幂等检查)，自动丢弃重复处理过的事件。
    *   后端增加 `version` 字段，作为单一数据源的权威版本。
*   **连接保活**:
    *   实现 WebSocket `ping/pong` 心跳机制。
    *   后端后台任务定期清理僵尸连接。
*   **防御性限制**:
    *   **人数限制**: 单房间最大 50 人。
    *   **数据限制**: 单房间最大 200 条事项，单条文本最大 500 字符。
    *   **错误反馈**: 增加 `error` 事件类型，当前端触发限制时弹窗提示。
*   **体验优化**:
    *   前端重连后自动拉取最新 Snapshot 覆盖本地状态，确保断网重连后数据绝对一致。

---

## Phase 3: 数据持久化 (Database Persistence)
**时间**: 2026-02-05
**目标**: 接入真实数据库，确保服务重启或重新部署后数据不丢失。

### 核心产出
*   **技术选型**:
    *   **Database**: Supabase (PostgreSQL)，使用 Session Pooler 模式 (Port 5432) 兼容 IPv4。
    *   **ORM**: `SQLModel` (结合 Pydantic 与 SQLAlchemy)。
    *   **Driver**: `asyncpg` (高性能异步驱动)。
*   **后端重构**:
    *   `models.py`: 定义 `Room` 和 `TodoItem` 数据库表结构。使用 `BigInteger` 解决毫秒级时间戳溢出问题。
    *   `database.py`: 封装异步数据库引擎与 Session 管理。
    *   `main.py`: 彻底移除内存存储，全量迁移至数据库 CRUD 操作。引入 `IntegrityError` 处理机制，解决并发创建房间时的 Race Condition。
*   **架构调整**:
    *   实现启动时自动建表 (`init_db`)。
    *   在内存中保留 `Idempotency Cache` 以维持 MVP 的高性能去重。

---

## Phase 4: 极简权限与工程化交付 (Minimalist Auth & Delivery)
**时间**: 2026-02-05
**目标**: 构建无账号的 Token 鉴权体系，完善用户体验与错误处理，并实现 Docker 化部署。

### 核心产出
*   **极简权限体系**:
    *   **后端**: 实现了 `POST /api/rooms` 生成 Admin/Join Token；WebSocket 握手强制鉴权；区分 Admin/Member 角色。
    *   **前端**: 实现了 `<RoomGate />` 门禁组件，支持粘贴链接解锁；自动识别 Admin 身份并显示管理按钮。
*   **用户体验 (UX) 升级**:
    *   **错误处理**: 新增 `<RoomError />` 全屏组件，优雅处理 404/401 错误。
    *   **状态反馈**: 增加 WebSocket 加载中 (Loading Spinner) 和断线重连 (Reconnecting Banner) 的视觉反馈。
    *   **生命周期**: 后端实现了自动清理过期房间 (TTL: 24h) 的后台任务。
*   **工程化交付**:
    *   **Dockerization**: 创建了 `backend/Dockerfile`, `frontend/Dockerfile` (Multi-stage), 和 `docker-compose.yml`。
    *   **文档**: 更新 README 包含部署指南。

---

## Phase 4.1: 用户留存与体验优化 (User Retention & UX)
**时间**: 2026-02-05
**目标**: 提升用户“回头率”，优化清单管理体验。

### 核心产出
*   **最近访问列表**:
    *   前端重构 `store.ts`，支持存储房间名、权限 Token 和访问时间。
    *   首页新增“Recent Rooms”模块，展示历史访问记录，支持一键免鉴权跳转。
*   **智能排序**:
    *   后端优化 `get_room_snapshot`，实现“未完成置顶、已完成沉底”的自动排序。
*   **实用工具**:
    *   **文本复制**: 房间页新增复制按钮，支持一键导出格式化清单文本。

---

## Next Steps (待办规划)
*   [ ] **更多功能**: 支持置顶、标签颜色等。
*   [ ] **性能优化**: 引入 Redis 替代内存缓存 (如果需要水平扩展)。
---

## Phase 4.2: 工程上下文文档对齐 (AGENTS Sync)
**时间**: 2026-02-06
**目标**: 让 `AGENTS.md` 与当前实现保持一致，减少新协作者误判和上下文偏差。

### 核心产出
*   **技术栈对齐**: 明确后端已使用 PostgreSQL + SQLModel，不再是内存存储。
*   **鉴权与协作机制对齐**: 补充 token 邀请模型、角色权限与快照同步策略。
*   **运行与配置对齐**: 增补后端 `DATABASE_URL`、前端 `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL`。
*   **测试入口补齐**: 增加单测、e2e、压测命令，便于快速验证改动。
*   **风险自检清单**: 新增 WebSocket 异常、payload 边界、token 轮换一致性等高风险检查项。

---

## Phase 4.3: 稳定性缺陷修复与回归测试补齐
**时间**: 2026-02-06
**目标**: 修复 WebSocket 边界条件与重连生命周期问题，并补充对应测试。

### 核心产出
*   **WebSocket payload 防御性修复**: 增加 `parse_event_message`，统一处理缺失/非法 payload，避免 `payload=None` 时直接抛异常断连。
*   **item_edit 逻辑修复**: 增加 `apply_item_edit`，支持“仅更新 priority”场景，避免被 `text` 分支短路。
*   **前端重连生命周期修复**: 为重连定时器增加 `ref` 持有和卸载清理，避免重复重连和组件卸载后残留连接。
*   **CORS 配置收敛**: 改为通过 `CORS_ALLOW_ORIGINS` 配置白名单，默认仅本地开发域名；`allow_credentials` 与通配符解耦。
*   **测试补齐**:
    *   新增 `backend/tests/test_event_handling.py`，覆盖 payload 缺失、`clientEventId` 提取、priority-only 编辑、CORS 默认值。
    *   保持 `backend/tests/test_priority.py` 回归通过。
