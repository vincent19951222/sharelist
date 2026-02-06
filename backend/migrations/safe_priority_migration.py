"""
安全的优先级字段迁移 - 零停机、可回滚

策略：
1. 添加可选字段（已完成）
2. 后台逐步回填数据
3. 验证所有数据都有值
4. 添加 NOT NULL 约束
"""

import asyncio
from typing import Optional
from sqlmodel import Session, select
from backend.models import TodoItem
from backend.database import get_session
import logging

logger = logging.getLogger(__name__)


class PriorityMigration:
    """安全迁移管理器"""

    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size

    async def backfill_data(self, session: Session) -> dict:
        """
        后台回填数据
        分批处理，避免锁表
        """
        result = {
            "total_items": 0,
            "null_count": 0,
            "updated_count": 0,
            "errors": []
        }

        try:
            # 统计总数
            all_items = session.exec(select(TodoItem)).all()
            result["total_items"] = len(all_items)

            # 找出 NULL 的项
            null_items = [item for item in all_items if item.priority is None]
            result["null_count"] = len(null_items)

            logger.info(f"Found {len(null_items)} items with NULL priority")

            # 分批更新
            for i in range(0, len(null_items), self.batch_size):
                batch = null_items[i:i + self.batch_size]

                for item in batch:
                    try:
                        # 智能默认值策略
                        default_priority = self._infer_priority(item)
                        item.priority = default_priority
                        session.add(item)
                        result["updated_count"] += 1

                    except Exception as e:
                        error_msg = f"Failed to update item {item.id}: {str(e)}"
                        result["errors"].append(error_msg)
                        logger.error(error_msg)

                # 每批提交一次
                session.commit()
                logger.info(f"Updated batch {i//self.batch_size + 1}: {len(batch)} items")

        except Exception as e:
            session.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise

        return result

    def _infer_priority(self, item: TodoItem) -> str:
        """
        智能推断默认优先级

        策略：
        - 已完成的任务 → low
        - 未完成的任务 → medium
        """
        if item.done:
            return "low"
        else:
            return "medium"

    async def verify_no_nulls(self, session: Session) -> bool:
        """验证所有数据都有 priority 值"""
        null_items = session.exec(
            select(TodoItem).where(TodoItem.priority.is_(None))
        ).all()

        if len(null_items) > 0:
            logger.warning(f"Still have {len(null_items)} items with NULL priority")
            return False

        logger.info("✓ All items have priority value")
        return True

    async def add_not_null_constraint(self, session: Session):
        """
        添加 NOT NULL 约束
        只有在 verify_no_nulls() 通过后才应该调用
        """
        try:
            # 先设置默认值（确保新插入的数据不会 NULL）
            session.exec("ALTER TABLE todoitem ALTER COLUMN priority SET DEFAULT 'medium'")

            # 添加 NOT NULL 约束
            session.exec("ALTER TABLE todoitem ALTER COLUMN priority SET NOT NULL")

            session.commit()
            logger.info("✓ NOT NULL constraint added successfully")

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add NOT NULL constraint: {str(e)}")
            raise


async def run_migration():
    """执行完整迁移流程"""

    migration = PriorityMigration(batch_size=1000)

    with get_session() as session:
        # Step 1: 数据回填
        logger.info("=== Step 1: Backfilling data ===")
        result = await migration.backfill_data(session)

        print(f"""
        Migration Summary:
        - Total items: {result['total_items']}
        - NULL items found: {result['null_count']}
        - Updated: {result['updated_count']}
        - Errors: {len(result['errors'])}
        """)

        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")

        # Step 2: 验证
        logger.info("\n=== Step 2: Verifying no NULLs ===")
        verified = await migration.verify_no_nulls(session)

        if not verified:
            logger.error("❌ Verification failed! Cannot proceed to NOT NULL constraint")
            return False

        # Step 3: 添加 NOT NULL 约束（可选，需要手动确认）
        logger.info("\n=== Step 3: Ready for NOT NULL constraint ===")
        print("""
        ⚠️  Before adding NOT NULL constraint:
        1. Verify application works with new data
        2. Run tests
        3. Check logs for errors
        4. Then uncomment the line below

        To add NOT NULL constraint, uncomment:
        # await migration.add_not_null_constraint(session)
        """)

        # 取消注释下面的行来添加 NOT NULL 约束
        # await migration.add_not_null_constraint(session)

        return True


# 回滚脚本
async def rollback_migration(session: Session):
    """回滚到迁移前的状态"""
    try:
        # 移除 NOT NULL 约束
        session.exec("ALTER TABLE todoitem ALTER COLUMN priority DROP NOT NULL")

        # 移除默认值
        session.exec("ALTER TABLE todoitem ALTER COLUMN priority DROP DEFAULT")

        session.commit()
        logger.info("✓ Migration rolled back successfully")

    except Exception as e:
        session.rollback()
        logger.error(f"Rollback failed: {str(e)}")
        raise


if __name__ == "__main__":
    """运行迁移"""
    print("Starting priority field migration...")
    print("=" * 60)

    success = asyncio.run(run_migration())

    if success:
        print("\n✅ Migration completed successfully!")
        print("Next: Review the results and add NOT NULL constraint when ready")
    else:
        print("\n❌ Migration failed. Please check the logs.")
