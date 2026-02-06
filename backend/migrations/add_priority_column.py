"""
Migration: Add priority column to todoitem table
Version: 001
Date: 2025-02-06
"""

from sqlmodel import Session, select
from backend.models import TodoItem
import logging

logger = logging.getLogger(__name__)

def upgrade(session: Session):
    """
    Add priority column to todoitem table.
    Migration strategy:
    1. Add column as nullable first
    2. Backfill existing rows with "medium"
    3. Add NOT NULL constraint
    4. Add CHECK constraint for valid values
    """

    # Step 1: Add priority column (nullable first)
    logger.info("Adding priority column to todoitem table...")
    session.exec("""
        ALTER TABLE todoitem
        ADD COLUMN priority VARCHAR(10);
    """)

    # Step 2: Backfill existing rows with "medium"
    logger.info("Backfilling existing rows with 'medium' priority...")
    session.exec("""
        UPDATE todoitem
        SET priority = 'medium'
        WHERE priority IS NULL;
    """)

    # Step 3: Set NOT NULL constraint
    logger.info("Setting NOT NULL constraint...")
    session.exec("""
        ALTER TABLE todoitem
        ALTER COLUMN priority SET NOT NULL;
    """)

    # Step 4: Set DEFAULT value
    logger.info("Setting DEFAULT value to 'medium'...")
    session.exec("""
        ALTER TABLE todoitem
        ALTER COLUMN priority SET DEFAULT 'medium';
    """)

    # Step 5: Add CHECK constraint for valid values
    logger.info("Adding CHECK constraint for valid priorities...")
    session.exec("""
        ALTER TABLE todoitem
        ADD CONSTRAINT check_priority
        CHECK (priority IN ('high', 'medium', 'low'));
    """)

    session.commit()
    logger.info("✓ Migration completed successfully!")

def downgrade(session: Session):
    """
    Rollback: Remove priority column from todoitem table.
    """
    logger.info("Rolling back: Removing priority column...")

    # Drop the constraint first
    session.exec("""
        ALTER TABLE todoitem
        DROP CONSTRAINT IF EXISTS check_priority;
    """)

    # Drop the column
    session.exec("""
        ALTER TABLE todoitem
        DROP COLUMN priority;
    """)

    session.commit()
    logger.info("✓ Rollback completed!")

if __name__ == "__main__":
    # For manual testing
    from backend.database import get_session

    with get_session() as session:
        upgrade(session)
