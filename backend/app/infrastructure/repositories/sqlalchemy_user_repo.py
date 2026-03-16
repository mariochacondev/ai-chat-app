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

    async def create(self, email: str, hashed_password: str) -> User:
        async with self._session_factory() as session:
            model = UserModel(email=email, hashed_password=hashed_password)
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return User(
                id=model.id,
                email=model.email,
                hashed_password=model.hashed_password,
                is_active=model.is_active,
                created_at=model.created_at,
            )
