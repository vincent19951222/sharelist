from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from backend/.env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env file")

# Create Async Engine
# echo=True will log SQL queries to console (useful for debugging)
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Create Async Session Local
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Dependency to get DB session
async def get_db():
    async with async_session() as session:
        yield session

# Init DB (Create tables)
async def init_db():
    async with engine.begin() as conn:
        # In production, use Alembic for migrations.
        # For MVP, this creates tables if they don't exist.
        await conn.run_sync(SQLModel.metadata.create_all)
