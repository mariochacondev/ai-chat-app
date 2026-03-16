from fastapi import HTTPException, status
from app.infrastructure.security.jwt_tokens import JWTService

def get_user_id_from_raw_token(token: str) -> int:
    try:
        tokens = JWTService()
        payload = tokens.decode(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if payload.get("typ") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return int(sub)
