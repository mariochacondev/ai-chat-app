from abc import ABC, abstractmethod
from app.core.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def list_users(self):
        raise NotImplementedError

    @abstractmethod
    async def create(self, email: str, hashed_password: str, is_admin: bool = False) -> User:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        raise NotImplementedError