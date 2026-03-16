import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

def _split_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",")] if value else []

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "AI Chat")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = int(os.getenv("ACCESS_TOKEN_EXP_MIN", "15"))
    refresh_token_exp_minutes: int = int(os.getenv("REFRESH_TOKEN_EXP_MIN", str(60 * 24 * 14)))
    cors_origins: list[str] = _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173"))
    ollama_base: str = os.getenv("OLLAMA_BASE", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3:8b")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "docs")
    ollama_embed_model: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

settings = Settings()
