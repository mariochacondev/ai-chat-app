from fastapi import APIRouter, HTTPException
from app.infrastructure.repositories.sqlalchemy_user_repo import SQLAlchemyUserRepository
from app.infrastructure.security.passlib_hasher import PasslibHasher
from app.infrastructure.security.jwt_tokens import JWTService
from app.interfaces.http.schemas.auth import RegisterIn, TokenOut, RefreshIn

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