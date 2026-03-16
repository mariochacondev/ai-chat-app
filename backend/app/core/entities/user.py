from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: int | None
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime | None = None
