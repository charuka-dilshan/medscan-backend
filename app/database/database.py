import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Load environment variables from .env file
load_dotenv()

# 2. Database URL එක .env එකෙන් ලබා ගැනීම
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ ERROR: DATABASE_URL environment variable is not set in .env file!")

# 🔄 Supabase Free-Tier එකට ගැළපෙන පරිදි Asynchronous Engine එක සෑදීම
# pool_size=5: Supabase free limits ඉක්මවා නොයෑමට එකවර පවතින connections 5 කට සීමා කරයි.
# pool_pre_ping=True: Connection එක බිඳී ඇත්නම් හැම request එකකටම පෙර එය හඳුනාගෙන auto-reconnect කරයි.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Production වලදී console එක messy නොවීමට False කර ඇත (ඕනෙ නම් True කරන්න)
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

# 3. Asynchronous Database Sessions නිර්මාණය කරන Session Factory එක
async_session = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 4. SQLAlchemy Models නිර්මාණය කිරීමට පාවිච්චි කරන Base Class එක
Base = declarative_base()

# ==========================================
# 🔌 ASYNC DATABASE SESSION DEPENDENCY INJECTION
# ==========================================
async def get_db():
    """
    FastAPI Endpoints වලට Asynchronous DB Session එකක් ලබා දෙන Dependency Injection එක.
    Request එක අවසන් වූ සැනින් 'async with' මඟින් connection එක ස්වයංක්‍රීයවම වසා දමයි (Close).
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()