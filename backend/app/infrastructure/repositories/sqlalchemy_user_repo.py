from sqlalchemy import select

from app.core.entities.user import User
from app.core.ports.user_repository import UserRepository
from app.infrastructure.db import SessionLocal
from app.infrastructure.models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    async def get_by_email(self, email: str):
        async with self._session_factory() as session:
            res = await session.execute(select(UserModel).where(UserModel.email == email))
            row = res.scalars().first()
            if not row:
                return None
            return User(
                id=row.id,
                email=row.email,
                hashed_password=row.hashed_password,
                is_active=row.is_active,
                created_at=row.created_at,
            )

    async def get_by_id(self, user_id: int) -> User | None:
        async with SessionLocal() as s:
            res = await s.execute(select(UserModel).where(UserModel.id == user_id))
            row = res.scalar_one_or_none()
            if not row:
                return None
            return User(
                id=row.id,
                email=row.email,
                hashed_password=row.hashed_password,
                is_active=row.is_active,
            )

    async def list_users(self) -> list[UserModel]:
        async with SessionLocal() as s:
            res = await s.execute(select(UserModel).order_by(UserModel.created_at.desc()))
            return list(res.scalars().all())

    async def create(self, email: str, hashed_password: str, is_admin: bool = False) -> User:
        async with SessionLocal() as s:
            row = UserModel(
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_admin=is_admin,
            )
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return User(
                id=row.id,
                email=row.email,
                hashed_password=row.hashed_password,
                is_active=row.is_active,
            )

    async def delete(self, user_id: int) -> bool:
        async with SessionLocal() as s:
            res = await s.execute(select(UserModel).where(UserModel.id == user_id))
            row = res.scalar_one_or_none()
            if not row:
                return False
            await s.delete(row)
            await s.commit()
            return True
