from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rate_limit import rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models import User, UserRole
from app.schemas.auth import AuthResponse, RefreshRequest, UserLogin, UserPublic, UserRegister

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=AuthResponse, dependencies=[Depends(rate_limit(limit=10, window_seconds=60))])
async def register_user(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    email = str(payload.email).lower()
    username = payload.username.strip()
    existing = await db.scalar(
        select(User).where(or_(User.email == email, User.username == username))
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already registered")

    user = User(
        email=email,
        username=username,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole.buyer.value,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(
        token=create_access_token(user.email, user.token_version),
        refresh_token=create_refresh_token(user.email, user.token_version),
        user=UserPublic(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
        ),
    )


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(rate_limit(limit=20, window_seconds=60))])
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    email = str(payload.email).lower()
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is suspended")
    return AuthResponse(
        token=create_access_token(user.email, user.token_version),
        refresh_token=create_refresh_token(user.email, user.token_version),
        user=UserPublic(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
        ),
    )


@router.get("/me", response_model=UserPublic)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=AuthResponse)
async def refresh_session(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        claims = decode_refresh_token(payload.refresh_token)
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    email = claims.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")
    user = await db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or claims.get("ver", 0) != user.token_version:
        raise HTTPException(status_code=401, detail="Refresh token is no longer valid")
    return AuthResponse(
        token=create_access_token(user.email, user.token_version),
        refresh_token=create_refresh_token(user.email, user.token_version),
        user=UserPublic(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        ),
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current_user.token_version += 1
    await db.commit()
    return {"message": "Logged out successfully"}
