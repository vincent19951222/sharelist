# ShareList 数据库迁移策略

## 当前状态
- ✅ priority 字段已添加（Optional）
- ✅ 代码兼容 NULL 值
- ✅ 向后兼容，不破坏现有功能

## 推荐的渐进式迁移计划

### Phase 1: 代码层兼容（已完成）✅
```python
# models.py
priority: Optional[str] = Field(default="medium", nullable=True)

# 代码处理 NULL
def get_safe_priority(item):
    return item.priority or "medium"
```

**状态**: ✅ 完成
**影响**: 无破坏性变更

---

### Phase 2: 观察期（当前）📊
```bash
# 监控指标
- 优先级功能使用率
- 错误日志中是否有 priority 相关问题
- 性能影响（NULL 值查询）
```

**时间**: 运行 1-2 周

**决定**: 如果没问题，进入 Phase 3

---

### Phase 3: 后台数据回填（可选）
```bash
# 运行安全迁移脚本
cd backend
python migrations/safe_priority_migration.py

# 该脚本会：
# 1. 分批更新 NULL 值
# 2. 智能推断默认值
# 3. 记录详细日志
# 4. 可以随时中断
```

**时机**:
- 流量低峰期
- 有回滚准备
- 充分测试后

---

### Phase 4: 添加 NOT NULL 约束（可选）
```sql
-- 只有在确认所有数据都有值后才执行
ALTER TABLE todoitem
ALTER COLUMN priority SET NOT NULL;
```

**前提条件**:
- ✅ Phase 3 完成
- ✅ 所有数据都有 priority 值
- ✅ 代码已经稳定运行 2 周以上

---

## 其他数据库字段的最佳实践

### 1. 添加新字段
```python
# ✅ 推荐: Optional + 默认值
new_field: Optional[str] = Field(default="default_value", nullable=True)
```

### 2. 修改字段类型
```python
# ❌ 危险: 直接改类型
field: int  # 以前是 str

# ✅ 安全: 添加新字段，逐步迁移
old_field: str  # 保留
new_field: int  # 新增
# 在代码中处理两个字段
```

### 3. 删除字段
```python
# 步骤:
# 1. 代码停止使用字段（但不删除）
# 2. 观察 1-2 周
# 3. 确认没有问题后，从模型中删除
# 4. 最后从数据库删除
```

---

## 回滚计划

### 如果迁移出问题：
```python
# 立即回滚代码
git revert <commit>

# 或者保持 Optional 字段
# 不执行 NOT NULL 约束
# NULL 值继续被代码处理为默认值
```

---

## 工具推荐

### 1. Alembic（Python 数据库迁移工具）
```bash
# 安装
pip install alembic

# 初始化
alembic init migrations

# 创建迁移
alembic revision --autogenerate -m "add priority"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

**优点**:
- 版本控制
- 自动回滚
- 迁移历史

---

### 2. Supabase Migrations
```sql
-- migrations/001_add_priority.sql
-- Up
ALTER TABLE todoitem ADD COLUMN priority VARCHAR(10);

-- Down
ALTER TABLE todoitem DROP COLUMN priority;
```

---

## 总结

### 对于 ShareList 项目：
1. ✅ **当前实现已经很好** - Optional 字段 + 代码兼容
2. 📊 **观察 1-2 周** - 确认没有问题
3. 🔄 **可选：后台回填** - 如果想规范化数据
4. 🔒 **可选：NOT NULL** - 只在确认所有数据都有值后

### 核心原则：
- 🛡️ **向后兼容优先** - 不破坏现有功能
- 📈 **渐进式变更** - 分步骤，可回滚
- 🧪 **充分测试** - staging → production
- 📝 **记录一切** - 迁移日志、回滚脚本

### 何时需要 NOT NULL：
- 数据量大（>100万行），查询性能重要
- 需要强数据一致性
- 团队协作，需要强制约束

### 何时可以保持 Optional：
- 个人项目或小团队
- 数据量小（<10万行）
- 性能不是瓶颈
- 代码层已经很好地处理了 NULL

---

_更新日期: 2026-02-06_
_项目: ShareList (Room Todo)_
_变更: add-priority feature_
