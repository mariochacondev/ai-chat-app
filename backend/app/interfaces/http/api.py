from fastapi import APIRouter
from .routers import auth, chat, docs_upload, conversations

api = APIRouter()
api.include_router(auth.router)
api.include_router(chat.router)
api.include_router(docs_upload.router)
api.include_router(conversations.router)


