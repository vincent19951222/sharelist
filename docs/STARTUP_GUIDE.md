# 🚀 启动与环境变量说明 (Startup Guide)

本文档旨在帮助开发者快速搭建和运行 ShareList 项目。

---

## 1. 环境要求
*   **Node.js**: v18.0.0 或更高版本
*   **Python**: v3.8 或更高版本 (仅后端需要)
*   **包管理器**: npm 或 yarn

## 2. 快速启动 (开发模式)

我们在 `package.json` 中配置了一键启动命令，可同时运行前端 (Next.js) 和后端 (FastAPI)。

```bash
# 1. 一键安装所有依赖 (根目录执行)
npm run install:all

# 2. 准备本地环境文件
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 3. 启动全栈开发环境
npm run dev
```

*   **前端地址**: [http://localhost:3000](http://localhost:3000)
*   **后端地址**: [http://localhost:8000](http://localhost:8000)
*   **API 文档**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

---

## 3. 环境变量配置

项目支持通过后端 `backend/.env` 与前端 `frontend/.env.local` 配置环境变量。

### 推荐策略

*   **本地开发**: 使用 SQLite，零外部依赖，启动最快。
*   **远端部署 / 联调**: 使用 Supabase PostgreSQL，保留云端数据库路线。

### 后端变量

在 `backend/` 目录中创建 `.env` 文件：

| 变量名 | 本地默认值 | 说明 |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./sharelist.db` | 本地开发默认数据库。 |
| `CORS_ALLOW_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | 可选，跨域白名单。 |

**本地 SQLite 示例**:
```env
DATABASE_URL=sqlite+aiosqlite:///./sharelist.db
```

**远端 Supabase / PostgreSQL 示例**:
```env
DATABASE_URL=postgresql+asyncpg://postgres.<project-ref>:<password>@<pooler-host>:5432/postgres
```

### 前端变量
在 `frontend/` 目录中创建 `.env.local` 文件：

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | REST API 地址。 |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | WebSocket 服务地址。**局域网测试时请设为本机 IP** (如 `ws://192.168.1.5:8000`) |

**示例 `.env.local`**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://192.168.1.5:8000
```

> **注意**: 修改环境变量后需要重启 `npm run dev` 才能生效。

### 双数据库注意事项

*   应用运行时通过 `DATABASE_URL` 自动切换数据库类型，不需要改业务代码。
*   `scripts/db_tool.py` 只支持 PostgreSQL / Supabase 备份恢复，不支持本地 SQLite。
*   `backend/migrations/` 目录下的手工迁移脚本以 PostgreSQL 方言为主；本地 SQLite 开发通常直接依赖启动时自动建表。

---

## 4. 局域网真机测试指南

如果你想用手机连接电脑进行测试：

1.  **获取 IP**: 在电脑终端运行 `ipconfig` (Windows) 或 `ifconfig` (Mac/Linux) 获取局域网 IP (例如 `192.168.1.5`)。
2.  **启动后端**: 确保后端绑定在 `0.0.0.0` 或包含该 IP (目前默认开发命令已支持)。
3.  **配置前端**: 在 `frontend/` 目录新建 `.env.local`，填入 `NEXT_PUBLIC_API_URL=http://192.168.1.5:8000` 和 `NEXT_PUBLIC_WS_URL=ws://192.168.1.5:8000`。
4.  **重启服务**: 运行 `npm run dev`。
5.  **手机访问**: 手机浏览器打开 `http://192.168.1.5:3000`。

---

## 5. 项目结构
```
sharelist/
├── backend/            # Python FastAPI 后端
│   ├── main.py         # 后端入口与逻辑
│   └── requirements.txt
├── frontend/           # Next.js 前端源码
│   ├── src/            # 源码
│   ├── public/         # 静态资源
│   └── package.json    # 前端依赖
├── docs/               # 项目文档
│   ├── EVENT_PROTOCOL.md
│   ├── QA_CHECKLIST.md
│   └── STARTUP_GUIDE.md
└── package.json        # 根目录编排脚本
```
