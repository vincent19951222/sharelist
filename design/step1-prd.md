产品名与一句话
Room Todo：用一个房间码把多人拉进同一份清单，大家对同一份 checklist 共同新增和勾选。

目标用户与核心场景
用户：出行的朋友小团体，合租室友，活动组织者。
场景：旅行出发前准备清单，采购清单，活动物料清单，家务轮值清单。

MVP 目标
10 秒创建房间并获得房间码或链接。
朋友 10 秒加入房间并看到同一份清单。
新增事项与勾选事项的体验顺手，手机端优先。

范围定义
MVP 要做

创建房间，生成 roomId

加入房间，填写昵称

房间内清单 CRUD：新增，勾选完成，编辑文本，删除

显示完成者 doneBy

隐藏已完成开关

分享能力：复制 roomId，复制链接，支持系统分享就用系统分享

本地持久化：刷新页面数据不丢

MVP 暂时不做
登录注册与账号体系
复杂权限，例如只有房主能删别人事项
离线协同与冲突合并算法
推送通知
图片附件与语音输入
二维码生成与扫码加入
模板商店与公共模板库

页面与信息架构
页面 1：入口页
组件与字段：昵称输入，创建房间按钮，加入房间输入框与加入按钮
行为：
创建房间：生成 roomId，初始化空房间，跳转房间页
加入房间：带 roomId 跳转房间页
可选增强：展示最近加入过的房间列表，先放到后续迭代

页面 2：房间页
顶部区域：房间名，roomId，当前昵称，复制与分享按钮
列表区域：事项列表，每条含勾选框，文本，完成者信息，删除入口，编辑入口
底部区域：新增输入框与添加按钮
辅助功能：隐藏已完成，显示总数与已完成数

核心用户流程
创建房间流程：入口页输入昵称，点击创建房间，进入房间页，开始添加事项，分享链接给朋友
加入房间流程：入口页输入昵称，输入 roomId 或打开分享链接，进入房间页，参与新增与勾选

数据模型定义
Room
roomId: string
roomName: string
createdAt: number
updatedAt: number

Member
memberId: string
name: string
joinedAt: number

TodoItem
id: string
text: string
done: boolean
doneBy: string 可空
createdAt: number
updatedAt: number

事件模型建议，先写出来方便后面接后端
ItemAdd: item
ItemToggle: itemId, done, doneBy
ItemEdit: itemId, text
ItemDelete: itemId

前端架构建议
技术：Next.js App Router，TypeScript，Tailwind
目录建议：
src/app 放路由页面
src/components 放复用组件
src/lib 放纯逻辑与存储封装
状态管理建议：
MVP 阶段用 useReducer 或 Zustand 二选一都行
RoomState 作为单一真相源
持久化：
localStorage 按 roomId 存一份 RoomState
用户昵称单独存一份 LocalUser

后端架构规划，写进 PRD 让方向一致
阶段 1 只做前端本地版，不启后端
阶段 2 上 FastAPI 与 WebSocket，先内存存房间状态，广播事件
阶段 3 上 Postgres，房间与事项落库，事件表可选用于回放与排查

验收标准

任意设备打开入口页，输入昵称后可创建房间并进入房间页

房间页可以新增事项，列表立即出现

勾选事项后显示完成状态，并记录完成者昵称

双击或点击进入编辑后可修改文本，保存生效

删除事项后列表移除

隐藏已完成切换后已完成事项可隐藏与显示

刷新页面后数据仍存在

复制 roomId 与复制链接可用，系统分享可用则触发