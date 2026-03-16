from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.settings import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev convenience: auto-create tables. For production, use Alembic migrations.
    from app.infrastructure.models import UserModel  # noqa: F401
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print("DB init failed:", repr(e))
    yield
