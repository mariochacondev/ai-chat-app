from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import ConversationModel, ChatMessageModel

async def get_or_create_conversation(
    db: AsyncSession,
    user_id: int,
    conversation_id: int | None,
) -> ConversationModel:
    if conversation_id is not None:
        res = await db.execute(
            select(ConversationModel).where(
                ConversationModel.id == conversation_id,
                ConversationModel.user_id == user_id,
            )
        )
        convo = res.scalar_one_or_none()
        if convo:
            return convo

    convo = ConversationModel(user_id=user_id, title="New chat")
    db.add(convo)
    await db.flush()  # convo.id available
    return convo

async def add_message(
    db: AsyncSession,
    conversation_id: int,
    role: str,
    content: str,
) -> ChatMessageModel:
    msg = ChatMessageModel(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)
    return msg

async def get_recent_messages(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 20,
) -> list[ChatMessageModel]:
    # Most recent N, then reverse to chronological
    res = await db.execute(
        select(ChatMessageModel)
        .where(ChatMessageModel.conversation_id == conversation_id)
        .order_by(ChatMessageModel.id.desc())
        .limit(limit)
    )
    rows = list(res.scalars().all())
    rows.reverse()
    return rows