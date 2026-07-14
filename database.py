import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# ⚠️ මතක ඇතුව ඔයාගේ .env එකේ DATABASE_URL එක async සඳහා "postgresql+asyncpg://..." ලෙස තිබිය යුතුය.
DATABASE_URL = os.getenv("DATABASE_URL")

# Supabase free-tier connection සීමාව ඉක්මවා නොයෑමට pool_size එක 5 කට සීමා කරයි 
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    pool_size=5,
    max_overflow=10
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# FastAPI Endpoint Injection එක සඳහා Asynchronous DB Session එක
async def get_db():
    async with async_session() as session:
        yield session