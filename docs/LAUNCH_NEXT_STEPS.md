# 下一步：P0/P1 改动地图 与 可上线产品规格草案

本文用于落地“上线可用”目标的下一步工作内容。  
相关文档：`docs/LAUNCH_READINESS.md`，`docs/QA_CHECKLIST.md`

---

## 1) P0/P1 改动地图（What/Where/Why）

### P0-1 加入流程与权限一致化

目标：roomId 与 token 心智对齐，避免“只有房间码无法加入”的断流程  
产品方向结论：私密邀请为主，必须 token 才可加入

核心心智  
对外：必须邀请链接或邀请码才能进入  
对内：roomId 只是路由标识，不是入场凭证

体验风险与对应  
风险：用户只拿到 roomId 会卡死  
对应：所有入口都强调“邀请码为主”，并提供一键复制邀请链接或邀请码

体验与文案原则  
首页加入区提示 “房间码/链接” 应替换为 “邀请码/链接”  
房间页顶部清晰展示 “邀请信息”，并提供复制  
RoomGate 文案强调 “此房间是私密的，需要邀请码”

协议与文档对齐点  
WebSocket URL 必须携带 token，文档显式强调  
snapshot 中的 role/joinToken 字段文档化  
README 说明 “roomId 不是邀请码”

QA Checklist 需要补充  
仅 roomId 访问时进入 RoomGate 并提示需要邀请码  
复制邀请码/邀请链接必须显式可操作且可验证

可能影响文件  
`frontend/src/app/page.tsx`  
`frontend/src/app/room/[roomId]/page.tsx`  
`frontend/src/components/RoomGate.tsx`  
`docs/EVENT_PROTOCOL.md`  
`docs/QA_CHECKLIST.md`  
`README.md`

---

### P0-2 协议与文档对齐

目标：文档准确反映真实事件与参数，确保前后端与未来多端接入一致

当前缺口（以实际实现为准）  
WebSocket URL 必须携带 token（当前文档未写）  
实际事件缺失：`room_rename`、`room_clear_done`、`token_rotated`  
snapshot 实际包含字段：`role`、`joinToken`（当前文档未写）  
错误事件触发条件与 close code 未文档化（401/403/404/满员/过期）

文档对齐范围  
`docs/EVENT_PROTOCOL.md`  
`README.md`

需要补齐的协议细节  
WebSocket URL 规范：`ws://<host>:8000/ws/{roomId}/{userName}?token=...`  
Server->Client `snapshot` payload 中额外字段  
Admin-only 事件说明（rename/clear_done）  
Token 轮换相关事件与含义（`token_rotated`）  
WebSocket close code 与含义（401/403/404/满员/过期）

QA Checklist 需要补充  
token 缺失/错误时进入 RoomGate 或被拒绝  
token 轮换后旧 token 行为（提示需要新邀请）  
Admin-only 事件被 member 触发时的提示

---

### P0-3 部署与环境配置清晰

目标：上线时可复现、可部署、无歧义

当前风险  
后端强依赖 `DATABASE_URL`，未配置即启动失败  
README/Startup Guide 对生产部署与最小可用配置描述不一致  
Docker 一键部署的环境变量说明不完整

文档与部署对齐范围  
`docs/STARTUP_GUIDE.md`  
`README.md`  
`docker-compose.yml`

需要补齐的部署信息  
最小可用数据库配置示例（Supabase/本地 Postgres）  
部署所需环境变量清单（前端/后端）  
Docker 部署步骤与环境变量传入方式

关键决策点  
是否提供“无需数据库的 demo 模式”  
生产部署是否要求 HTTPS（影响 WS / WSS）  
是否需要区分开发/生产配置示例

---

### P0-4 生命周期告知

目标：明确 24h 过期规则，避免数据丢失投诉

当前风险  
过期策略仅在后端存在，前端无任何提示  
用户体验上会被理解为“数据丢失”

需要告知的内容  
“房间 24 小时无操作会自动清理”  
“可通过分享/收藏链接快速回访”

UI 告知位置建议  
房间页标题区（细小提示）  
分享动作后的提示文案  
RoomGate（首次进入时告知）

可能影响文件  
`frontend/src/app/room/[roomId]/page.tsx`  
`docs/QA_CHECKLIST.md`  
`README.md`

---

### P0-5 错误提示一致化

目标：房间不存在、已满、token 失效有一致反馈

当前风险  
WS close code 与前端提示不一致  
一部分错误仅 alert，体验割裂

需要统一的错误状态  
房间不存在 / 已过期  
token 无效 / 已轮换  
房间已满  
服务端不可达 / 断线重连

可能影响文件  
`frontend/src/app/room/[roomId]/page.tsx`  
`frontend/src/components/RoomError.tsx`  
`docs/QA_CHECKLIST.md`

---

### P1-1 权限 UI 反馈

目标：Admin/Member 权限差异可见

当前风险  
用户无法直观看到自己权限范围  
受限功能缺少灰化或提示，导致困惑

UI 反馈建议  
顶部显示角色徽章（Admin/Member）  
受限功能按钮显示“仅管理员”提示或禁用态  
提示文案统一（避免只有 alert）

可能影响文件  
`frontend/src/app/room/[roomId]/page.tsx`  
`docs/QA_CHECKLIST.md`

---

### P1-2 邀请安全控制

目标：房主可重新生成邀请 token

当前风险  
邀请一旦泄露无法收回  
现有 API 未暴露给前端

需要的用户能力  
Admin 可在房间内点击“重置邀请”  
重置后旧 token 失效，成员需重新加入

可能影响文件  
`frontend/src/app/room/[roomId]/page.tsx`  
`frontend/src/lib/api.ts`  
`backend/main.py`（已有 API，需要对齐前端）  
`docs/EVENT_PROTOCOL.md`  
`docs/QA_CHECKLIST.md`

---

### P1-3 连接状态反馈

目标：连接成功/断线/重连/离线操作明确

当前风险  
仅有断线 banner，没有“已连接”或“离线操作不可用”的反馈  
断线期间用户操作易丢失

体验建议  
顶部状态：Connected / Reconnecting / Offline  
离线时禁用新增/编辑/删除，并提示原因

可能影响文件  
`frontend/src/app/room/[roomId]/page.tsx`  
`docs/QA_CHECKLIST.md`

---

### P1-4 回访路径可靠

目标：Recent Rooms 可靠进入并提示 token 过期

当前风险  
Recent Rooms 依赖本地 token，过期后会失败且提示不清晰

需要补齐的体验  
Recent Rooms 进入失败时给出清晰提示  
token 过期 → 引导重新获取邀请

可能影响文件  
`frontend/src/app/page.tsx`  
`frontend/src/lib/store.ts`  
`docs/QA_CHECKLIST.md`

---

### P1-5 基础审计感

目标：协作时能感知他人操作

当前风险  
多人操作时缺乏“谁做了什么”的感知

最小可用建议  
已完成项展示 doneBy（已存在）  
关键操作提示（新增/删除/清理时的轻提示）

可能影响文件  
`frontend/src/app/room/[roomId]/page.tsx`  
`docs/EVENT_PROTOCOL.md`

---

## 2) 可上线产品规格草案（细化版）

### 2.1 产品目标与定位

一句话：ShareList 是一个无需登录、通过私密邀请快速协作的实时清单工具  
目标体验：5 分钟内完成 “创建 → 分享 → 加入 → 同步”  
核心价值：低摩擦、即时协作、私密可控

### 2.2 关键用户与角色

Admin：创建房间者，拥有完全控制权限  
Member：通过邀请加入，可编辑清单项  
Guest：未授权用户，仅能看到 RoomGate

### 2.3 核心流程（可上线闭环）

创建房间：输入昵称 → 创建房间 → 获取 Admin Token → 进入房间  
加入房间：必须通过邀请链接或邀请码 → 进入房间（Member）  
协作使用：新增/编辑/完成/删除 → 服务端广播 snapshot → 端间一致  
分享与控制：Admin 可随时重置邀请，旧邀请失效

### 2.4 业务规则（必须清晰对外）

房间人数上限 50  
事项数量上限 200  
文本长度上限 500  
房间 24 小时无操作将自动过期  
所有修改事件必须携带 clientEventId（幂等）

### 2.5 权限与安全

WebSocket 连接必须携带 token  
Admin 权限：重命名房间、清理已完成、重置邀请  
Member 权限：新增/编辑/完成/删除清单项  
安全心智：roomId 不是邀请码，必须 token 才能进入

### 2.6 连接与协作体验

连接成功后下发完整 snapshot  
断线自动重连  
断线期间操作需明确提示失败或不可用  
连接状态可视化（Connected / Reconnecting / Offline）

### 2.7 错误与边界处理

房间不存在或过期：提示并引导返回首页  
房间已满：提示容量上限  
token 失效/已轮换：提示重新获取邀请  
服务不可达：提示重试与网络状态

### 2.8 数据与生命周期

房间无操作 24h 自动删除  
用户需在 UI 上明确看到生命周期提示  
分享链接建议用于回访入口

### 2.9 可观测性（最小可用）

连接数、事件数、广播数、错误数  
提供轻量统计接口（当前已有 `/sys/stats`）

### 2.10 非目标（当前不做）

账号体系与登录  
跨房间搜索  
完整操作历史与回滚  
复杂权限与组织体系

---

## 3) 功能需求清单 + 验收标准（上线版）

### FR-1 私密邀请加入（核心闭环）

需求  
必须通过邀请链接或邀请码（token）进入房间  
roomId 不可作为直接进入凭证

验收标准  
仅输入 roomId 时进入 RoomGate，并提示需要邀请码  
通过带 token 的邀请链接可直接进入房间  
输入邀请码可成功加入

### FR-2 创建房间与角色分配

需求  
创建房间后自动成为 Admin  
自动获得 Admin Token 与 Join Token

验收标准  
创建房间后进入房间且显示 Admin 标识  
分享时默认使用 Join Token

### FR-3 权限控制

需求  
Admin 可重命名、清理已完成、重置邀请  
Member 仅可新增/编辑/完成/删除

验收标准  
Member 触发管理员操作会得到明确提示  
Admin 操作在 UI 有明显入口

### FR-4 连接与协作体验

需求  
连接状态可视化（Connected / Reconnecting / Offline）  
断线期间禁止提交操作或提示失败

验收标准  
断线时出现明显提示  
断线期间操作不会静默失败

### FR-5 实时同步

需求  
任一客户端操作，所有客户端在 1 秒内同步  
Snapshot 为唯一真相

验收标准  
多端新增/编辑/删除/完成可同步  
后加入用户可看到最新完整清单

### FR-6 错误与边界处理

需求  
房间不存在/过期、房间已满、token 失效需明确提示

验收标准  
每种错误都有明确 UI 状态与文案

### FR-7 生命周期告知

需求  
24h 过期规则对用户可见

验收标准  
房间页/分享入口能看到清晰提示

### FR-8 邀请安全控制

需求  
Admin 可重置邀请，旧 token 失效

验收标准  
重置后旧链接无法进入  
新链接可加入

### FR-9 回访路径可靠

需求  
Recent Rooms 可快速回访，失败时有提示

验收标准  
token 过期时提示“需要新邀请”

### FR-10 协作感最小提示

需求  
能感知“谁做了什么”的最小提示

验收标准  
完成项展示 doneBy  
关键操作有轻提示（新增/删除/清理）

---

## 4) 任务列表（按优先级）

### P0 任务

T0-1 明确加入流程文案与入口：统一“邀请码/链接”心智  
T0-2 RoomGate 文案更新：强调私密邀请与邀请码  
T0-3 协议文档补齐：token、事件、snapshot 字段  
T0-4 错误状态统一：token 失效/房间满/不存在/过期  
T0-5 生命周期提示位置确定并写入 UI/文档  
T0-6 部署文档完善：环境变量与最小配置

### P1 任务

T1-1 权限 UI 反馈：角色可见、受限功能提示  
T1-2 邀请安全控制：Admin 重置邀请入口  
T1-3 连接状态提示：Connected/Reconnecting/Offline  
T1-4 回访失败提示：token 过期引导  
T1-5 协作感提示：轻量操作提示与 doneBy 明确
