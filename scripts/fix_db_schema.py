import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv
from pathlib import Path

# Load env
env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=env_path)
DATABASE_URL = os.getenv("DATABASE_URL")

async def fix_schema():
    print(f"Connecting to database...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Checking 'priority' column...")
        try:
            # Attempt to add the column. 
            await conn.execute(text("""
                ALTER TABLE todoitem 
                ADD COLUMN IF NOT EXISTS priority VARCHAR DEFAULT 'medium';
            """))
            print("✅ Column 'priority' added successfully.")
            
        except Exception as e:
            print(f"⚠️  Error: {e}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_schema())