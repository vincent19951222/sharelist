# 灾难恢复演练指南 (Disaster Recovery Runbook)

本文档描述了 ShareList 项目的数据库备份与恢复流程。旨在确保当发生数据丢失、误删或云服务故障时，我们能迅速恢复业务。

## 核心工具

我们使用 `scripts/db_tool.py` 脚本进行管理。该脚本通过 Docker 容器运行标准的 PostgreSQL 客户端工具 (`pg_dump`, `psql`)，因此**不需要**在宿主机安装数据库软件。

### 前置要求
*   [x] Docker Desktop 已安装并运行。
*   [x] Python 3.x 已安装。
*   [x] `backend/.env` 配置正确 (包含有效的 `DATABASE_URL`)。

---

## 🟢 Part 1: 数据备份 (Backup)

定期或在重大变更前执行备份。

### 执行命令
在项目根目录运行：
```bash
npm run db:backup
```

### 预期结果
1.  终端显示 `Connecting to aws-0-ap-south-1...`
2.  脚本自动在项目根目录创建 `backups/` 文件夹。
3.  生成文件：`backups/backup_YYYYMMDD_HHMMSS.sql`。
4.  终端显示 `✅ Backup successful!`。

---

## 🔴 Part 2: 恢复演练 (Disaster Simulation & Recovery)

**警告**: 恢复操作会**覆盖**目标数据库中的现有数据。请务必确认目标数据库正确。

### 场景 A: 误删数据恢复
假设您误删了一个重要的房间，需要回滚到昨晚的备份。

1.  **找到备份文件**: 确认 `backups/` 目录下有可用的 `.sql` 文件 (例如 `backup_20260205_120000.sql`)。
2.  **执行恢复**:
    ```bash
    # 语法: npm run db:restore <文件名>
    npm run db:restore backup_20260205_120000.sql
    ```
3.  **确认警告**: 脚本会提示 `WARNING: This will OVERWRITE the database`，输入 `CONFIRM` 并回车。
4.  **等待完成**: 终端显示 `✅ Restore successful!`。

### 场景 B: 迁移到新环境 (全链路演练)
假设 Supabase 原实例 (Instance A) 彻底损坏，我们需要迁移到新的 Supabase 实例 (Instance B)。

1.  **准备新环境**: 在 Supabase 面板创建一个新的 Project，获取新的 Connection String。
2.  **修改配置**: 编辑 `backend/.env`，将 `DATABASE_URL` 修改为**新实例**的地址。
3.  **执行恢复**: 运行 `npm run db:restore <最新的备份文件>`。
4.  **验证业务**: 
    *   启动应用: `npm run dev`
    *   访问之前的房间链接 (例如 `http://localhost:3333/room/XyZ123`)。
    *   **验收标准**: 房间存在，清单内容与备份时一致，权限正常。

---

## 🛠️ 故障排查

**Q: 提示 `Docker is not installed or not running`?**
A: 请启动 Docker Desktop。脚本依赖 Docker 来运行 pg_dump，以免去在 Windows 上配置 Postgres 环境的麻烦。

**Q: 提示 `Authentication failed`?**
A: 检查 `backend/.env` 中的密码是否正确，确保没有特殊字符导致 URL 解析错误。

**Q: 恢复时报错 `relation "room" already exists`?**
A: 正常现象。脚本默认使用 `--clean` 参数，会先尝试 DROP 旧表。如果只是警告可以忽略，只要最后显示 Successful 即可。

---

## 📝 演练记录

| 日期 | 演练人 | 场景 | 结果 | 耗时 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-02-05 | Gemini | 场景 A (模拟误删) | ✅ 成功 | 2min | 验证了从 SQL 文本恢复数据的完整性。 |
