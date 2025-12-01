from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.check import Check

from .database import get_session, init_db
from .models import User
from .schemas import EmailCheckResponse, SignupRequest, SignupResponse, UsernameCheckResponse
from .utils import email_exists, generate_unique_username, hash_password, sanitize_username_fragment, username_exists

router = APIRouter()
checker = Check()


@router.on_event("startup")
async def startup_event():
    await init_db()


@router.get("/health")
def health_check():
    return {"status": checker.checking(), "service": "mindshipping"}


@router.get("/info")
def service_info():
    return {
        "service": "mindshipping",
        "message": "MindShipping backend placeholder endpoint",
    }


@router.post("/auth/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup_user(
    payload: SignupRequest,
    session: AsyncSession = Depends(get_session),
):
    email = payload.email.strip().lower()
    fullname = payload.full_name.strip()

    if await email_exists(email, session):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    username = await generate_unique_username(email, session)
    password_hash = hash_password(payload.password)

    user = User(
        fullname=fullname,
        email=email,
        username=username,
        password_hash=password_hash,
        is_active=False,
        is_verified=False,
        profile_pic_url=None,
        bio="",
    )

    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not register user") from exc

    await session.refresh(user)

    return SignupResponse(
        success=True,
        message="User registered successfully",
        uid=str(user.uid),
        username=user.username,
    )


@router.get("/auth/check-email", response_model=EmailCheckResponse)
async def check_email(
    email: EmailStr = Query(..., description="Email to check"),
    session: AsyncSession = Depends(get_session),
):
    exists = await email_exists(str(email).lower(), session)
    return EmailCheckResponse(exists=exists)


@router.get("/auth/check-username", response_model=UsernameCheckResponse)
async def check_username(
    username: str = Query(..., min_length=3, max_length=40, description="Username in question"),
    session: AsyncSession = Depends(get_session),
):
    cleaned = sanitize_username_fragment(username)
    exists = await username_exists(cleaned, session)
    return UsernameCheckResponse(exists=exists)
