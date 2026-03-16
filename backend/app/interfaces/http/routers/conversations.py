from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import get_db
from app.deps import get_user_id_from_token
from app.infrastructure.models import ConversationModel, ChatMessageModel

router = APIRouter(prefix="/conversations", tags=["conversations"])

class CreateConversationOut(BaseModel):
    id: int
    title: str

@router.post("/create", response_model=CreateConversationOut)
async def create_conversation(
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
):
    convo = ConversationModel(user_id=user_id, title="New chat")
    db.add(convo)
    await db.commit()
    await db.refresh(convo)
    return {"id": convo.id, "title": convo.title}

@router.get("/list")
async def list_conversations(
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ConversationModel)
        .where(ConversationModel.user_id == user_id)
        .order_by(desc(ConversationModel.updated_at))
        .limit(100)
    )
    rows = res.scalars().all()
    return {
        "ok": True,
        "conversations": [
            {"id": c.id, "title": c.title, "updated_at": c.updated_at, "created_at": c.created_at}
            for c in rows
        ],
    }

@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id,
        )
    )
    convo = res.scalar_one_or_none()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    res2 = await db.execute(
        select(ChatMessageModel)
        .where(ChatMessageModel.conversation_id == conversation_id)
        .order_by(ChatMessageModel.id.asc())
        .limit(500)
    )
    msgs = res2.scalars().all()

    return {
        "ok": True,
        "conversation": {"id": convo.id, "title": convo.title},
        "messages": [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at} for m in msgs],
    }