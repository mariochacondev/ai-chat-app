from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from app.deps import require_admin
from app.infrastructure.db import SessionLocal
from app.infrastructure.models import UserModel
from app.infrastructure.security.passlib_hasher import PasslibHasher
from app.interfaces.http.schemas.auth import AdminCreateUserIn

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("")
async def list_users(_: int = Depends(require_admin)):
    async with SessionLocal() as s:
        res = await s.execute(select(UserModel).order_by(UserModel.created_at.desc()))
        users = res.scalars().all()

        return [
            {
                "id": u.id,
                "email": u.email,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "created_at": u.created_at,
            }
            for u in users
        ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(payload: AdminCreateUserIn, _: int = Depends(require_admin)):
    async with SessionLocal() as s:
        existing = await s.execute(select(UserModel).where(UserModel.email == payload.email))
        user = existing.scalar_one_or_none()
        hasher = PasslibHasher()

        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        new_user = UserModel(
            email=payload.email,
            hashed_password=hasher.hash(payload.password),
            is_active=True,
            is_admin=payload.is_admin,
        )

        s.add(new_user)
        await s.commit()
        await s.refresh(new_user)

        return {
            "id": new_user.id,
            "email": new_user.email,
            "is_active": new_user.is_active,
            "is_admin": new_user.is_admin,
            "created_at": new_user.created_at,
        }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, admin_user_id: int = Depends(require_admin)):
    if user_id == admin_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )

    async with SessionLocal() as s:
        res = await s.execute(select(UserModel).where(UserModel.id == user_id))
        user = res.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        await s.delete(user)
        await s.commit()