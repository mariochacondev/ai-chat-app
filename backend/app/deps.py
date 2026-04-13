from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.infrastructure.security.auth import get_user_id_from_raw_token
from sqlalchemy import select
from app.infrastructure.db import SessionLocal
from app.infrastructure.models import UserModel

bearer = HTTPBearer(auto_error=False)

def get_user_id_from_token(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> int:
    return get_user_id_from_raw_token(creds.credentials)

async def require_admin(user_id: int = Depends(get_user_id_from_token)) -> int:
    async with SessionLocal() as s:
        res = await s.execute(select(UserModel).where(UserModel.id == user_id))
        user = res.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin only",
            )

        return user_id