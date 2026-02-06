"""
Quick migration script to add priority column
Run this with: python -m migrations.run_migration
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, SQLModel, create_engine
from backend.models import TodoItem
from backend.database import get_session

def migrate():
    """Add priority column to existing database"""
    print("Starting migration...")

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    engine = create_engine(database_url)

    # Add priority column
    with Session(engine) as session:
        try:
            # Step 1: Add column (nullable first)
            print("Adding priority column...")
            session.exec("ALTER TABLE todoitem ADD COLUMN priority VARCHAR(10)")

            # Step 2: Backfill existing rows
            print("Backfilling existing rows with 'medium'...")
            session.exec("UPDATE todoitem SET priority = 'medium' WHERE priority IS NULL")

            # Step 3: Set NOT NULL
            print("Setting NOT NULL constraint...")
            session.exec("ALTER TABLE todoitem ALTER COLUMN priority SET NOT NULL")

            # Step 4: Set DEFAULT
            print("Setting DEFAULT value...")
            session.exec("ALTER TABLE todoitem ALTER COLUMN priority SET DEFAULT 'medium'")

            # Step 5: Add CHECK constraint
            print("Adding CHECK constraint...")
            session.exec("ALTER TABLE todoitem ADD CONSTRAINT check_priority CHECK (priority IN ('high', 'medium', 'low'))")

            session.commit()
            print("✓ Migration completed successfully!")
            return True

        except Exception as e:
            session.rollback()
            print(f"✗ Migration failed: {e}")
            return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
