## Why

当前“上线可用”目标与实际体验仍存在关键不一致：私密邀请加入心智不统一、协议与文档不一致、错误与生命周期提示缺失，导致核心流程断裂与用户误解。现在补齐 P0/P1 能够把产品从“能用”推进到“可上线可持续使用”。

## What Changes

- 统一私密邀请加入流程，明确 token 为唯一入场凭证
- 完善连接状态、错误状态与生命周期提示，使体验一致可预期
- 暴露并对齐邀请安全控制（重置邀请）
- 明确权限 UI 反馈与回访路径行为
- 同步协议文档与现有实现

## Capabilities

### New Capabilities

- `invite-only-access`: 私密邀请加入与邀请码/链接心智统一
- `connection-status-feedback`: 连接状态可视化与离线操作提示
- `error-state-handling`: 统一错误状态与用户反馈
- `room-lifecycle-notice`: 24h 过期规则的前端告知
- `invite-rotation-control`: 管理员重置邀请与旧 token 失效
- `role-visibility`: Admin/Member 权限差异的可见反馈
- `recent-room-revisit`: 回访路径的失败提示与引导
- `collaboration-hints`: 最小协作感提示（doneBy/轻提示）

### Modified Capabilities

<!-- none -->

## Impact

- Frontend：房间页与首页交互、RoomGate、状态与提示组件
- Backend：现有 API/WS 行为对齐文档（无需新核心逻辑）
- Docs：EVENT_PROTOCOL / QA_CHECKLIST / README / STARTUP_GUIDE
