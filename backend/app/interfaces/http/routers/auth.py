from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.security.passlib_hasher import PasslibHasher
from app.infrastructure.security.jwt_tokens import JWTService
from app.interfaces.http.schemas.auth import RegisterIn, TokenOut, RefreshIn
from app.deps import get_user_id_from_token
from app.infrastructure.repositories.sqlalchemy_user_repo import SQLAlchemyUserRepository
from app.infrastructure.db import SessionLocal
from app.infrastructure.models import UserModel
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=dict)
async def register(payload: RegisterIn):
    users = SQLAlchemyUserRepository()
    hasher = PasslibHasher()
    existing = await users.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already taken")
    created = await users.create(payload.email, hasher.hash(payload.password))
    return {"id": created.id, "email": created.email}

@router.post("/login", response_model=TokenOut)
async def login(payload: RegisterIn):
    users = SQLAlchemyUserRepository()
    hasher = PasslibHasher()
    tokens = JWTService()

    user = await users.get_by_email(payload.email)
    if not user or not hasher.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": tokens.create_access_token(sub=str(user.id)),
        "refresh_token": tokens.create_refresh_token(sub=str(user.id)),
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=TokenOut)
async def refresh(payload: RefreshIn):
    tokens = JWTService()

    try:
        token_data = tokens.decode(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if token_data.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    sub = token_data.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = tokens.create_access_token(sub=sub)
    return TokenOut(access_token=new_access, refresh_token=payload.refresh_token, token_type="bearer")


@router.get("/me")
async def me(user_id: int = Depends(get_user_id_from_token)):
    async with SessionLocal() as s:
        res = await s.execute(select(UserModel).where(UserModel.id == user_id))
        user = res.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
        }