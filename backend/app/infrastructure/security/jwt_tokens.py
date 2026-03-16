from datetime import datetime, timedelta, timezone
import jwt
from app.core.ports.token_service import TokenService
from app.settings import settings

class JWTService(TokenService):
    def create_access_token(self, sub: str, expires_delta: timedelta | None = None) -> str:
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_exp_minutes))
        to_encode = {"sub": sub, "exp": expire, "typ": "access"}
        return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def create_refresh_token(self, sub: str, expires_delta: timedelta | None = None) -> str:
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.refresh_token_exp_minutes))
        to_encode = {"sub": sub, "exp": expire, "typ": "refresh"}
        return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def decode(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
