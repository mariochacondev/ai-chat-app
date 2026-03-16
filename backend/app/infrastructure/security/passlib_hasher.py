from passlib.context import CryptContext
from app.core.ports.password_hasher import PasswordHasher

_pwd = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=64_000,
    argon2__parallelism=2,
)

class PasslibHasher(PasswordHasher):
    def hash(self, plain: str) -> str:
        return _pwd.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return _pwd.verify(plain, hashed)
