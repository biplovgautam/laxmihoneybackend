import re
import secrets
import string
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
USERNAME_ALPHABET = string.ascii_lowercase + string.digits


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def sanitize_username_fragment(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9._-]", "", value.lower())
    return cleaned or "user"


async def generate_unique_username(email: str, session: AsyncSession, max_attempts: int = 10) -> str:
    local_part = email.split("@", 1)[0]
    base_username = sanitize_username_fragment(local_part)
    candidate = base_username

    for _ in range(max_attempts):
        stmt = select(User).where(User.username == candidate)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none() is None:
            return candidate
        suffix = "".join(secrets.choice(USERNAME_ALPHABET) for _ in range(4))
        candidate = f"{base_username}{suffix}"

    # Fallback: force a random username if collisions persist
    return "user" + "".join(secrets.choice(USERNAME_ALPHABET) for _ in range(8))


async def username_exists(username: str, session: AsyncSession) -> bool:
    stmt = select(User).where(User.username == username.lower())
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def email_exists(email: str, session: AsyncSession) -> bool:
    stmt = select(User).where(User.email == email.lower())
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None
