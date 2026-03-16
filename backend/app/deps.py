from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.infrastructure.security.auth import get_user_id_from_raw_token

bearer = HTTPBearer(auto_error=False)

def get_user_id_from_token(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> int:
    return get_user_id_from_raw_token(creds.credentials)
