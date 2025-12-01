import os
from typing import AsyncGenerator

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("MINDSHIPPING_DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("MINDSHIPPING_DATABASE_URL is not set in the environment variables")


def _to_async_driver(url: str) -> str:
    sql_url = make_url(url)

    if not sql_url.drivername.startswith("postgresql"):
        return url

    query = dict(sql_url.query)
    if "sslmode" in query and "ssl" not in query:
        query["ssl"] = query.pop("sslmode")
    query.pop("channel_binding", None)

    async_url = sql_url.set(drivername="postgresql+asyncpg", query=query)
    return str(async_url)


ASYNC_DATABASE_URL = _to_async_driver(DATABASE_URL)
engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):  # type: ignore[misc]
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from . import models  # noqa: F401 - ensure models are imported before creating tables

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
