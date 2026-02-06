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

# 2. 启动全栈开发环境
npm run dev
```

*   **前端地址**: [http://localhost:3000](http://localhost:3000)
*   **后端地址**: [http://localhost:8000](http://localhost:8000)
*   **API 文档**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

---

## 3. 环境变量配置

项目支持通过 `.env.local` 文件配置环境变量。

### 前端变量
在 `frontend/` 目录中创建 `.env.local` 文件：

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | WebSocket 服务地址。**局域网测试时请设为本机 IP** (如 `ws://192.168.1.5:8000`) |

**示例 `.env.local`**:
```env
NEXT_PUBLIC_WS_URL=ws://192.168.1.5:8000
```

> **注意**: 修改环境变量后需要重启 `npm run dev` 才能生效。

---

## 4. 局域网真机测试指南

如果你想用手机连接电脑进行测试：

1.  **获取 IP**: 在电脑终端运行 `ipconfig` (Windows) 或 `ifconfig` (Mac/Linux) 获取局域网 IP (例如 `192.168.1.5`)。
2.  **启动后端**: 确保后端绑定在 `0.0.0.0` 或包含该 IP (目前默认开发命令已支持)。
3.  **配置前端**: 在 `frontend/` 目录新建 `.env.local`，填入 `NEXT_PUBLIC_WS_URL=ws://192.168.1.5:8000`。
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