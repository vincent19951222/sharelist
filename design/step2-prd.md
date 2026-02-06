阶段 2 的 MVP scope 建议这样写进 PRD
做
1）服务端内存存储 roomId 对应的 RoomState
2）WebSocket 连接后服务端下发 snapshot
3）客户端发送事件 item_add item_toggle item_edit item_delete
4）服务端校验与补全元数据 updatedAt doneBy 然后广播给同房间所有连接
5）断线重连后客户端自动重新拉 snapshot
6）房间可选做一个 TTL，比如 24 小时无访问就丢弃，省事省内存

不做
登录注册
数据库持久化
复杂权限与冲突合并
离线编辑后合并
推送通知

架构选型给你两个现实路线
路线 A：独立 FastAPI 服务做 WebSocket，Next.js 继续只负责前端
优点是和你 PRD 规划一致，逻辑清晰，后续接 Postgres 很自然
路线 B：在 Next.js 里加一个常驻 Node WebSocket 服务
优点是仓库看起来更一体化
缺点是如果你以后部署到偏 serverless 的平台，WebSocket 常驻连接会比较麻烦

你现在用 coding agent，路线 A 通常更省心，因为边界清楚，调试也直观。

你可以直接把下面这段丢给 coding agent，当作阶段 2 的实现说明书
“进入阶段 2，实现真正跨设备协同。保持现有 Next.js 前端 UI 不大改。新增一个后端服务用于多人同步，优先用 FastAPI。后端用内存 Map 保存 roomId 到 RoomState。提供一个 WebSocket 端点 ws 连接参数包含 roomId 和 userName。连接成功后服务端发送 snapshot 事件，内容是当前 RoomState。前端本地的每次操作改成发送事件到 ws，由服务端校验与补充 updatedAt 和 doneBy，并广播给同房间所有客户端。客户端收到事件后更新本地状态并渲染。实现断线自动重连，重连后再次请求 snapshot 保证一致。暂不接数据库与登录，不做复杂权限。交付物包含：后端启动方式，前后端同时启动的开发脚本，事件协议文档，手工验收步骤，两台设备协同演示。”

事件协议建议你让 agent 固化成一个文件，避免口口相传
client to server
type: item_add payload: { text }
type: item_toggle payload: { itemId, done }
type: item_edit payload: { itemId, text }
type: item_delete payload: { itemId }

server to client
type: snapshot payload: RoomState
type: room_event payload: { event, roomStateVersion 或 updatedAt }
也可以直接广播最新 RoomState，简单粗暴，先跑通再优化

手工验收的硬指标
两台手机连同一个后端地址
手机 A 创建房间后把 roomId 发给手机 B
手机 B 加入后立刻看到同一份清单
A 新增一条，B 1 秒内出现
B 勾选完成，A 1 秒内显示完成者昵称
任意一方刷新页面，仍能从服务端拿到最新状态