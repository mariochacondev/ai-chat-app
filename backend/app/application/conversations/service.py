from __future__ import annotations

from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import ConversationModel, ChatMessageModel


async def get_or_create_conversation(
    db: AsyncSession,
    user_id: int,
    conversation_id: Optional[int],
) -> ConversationModel:
    """
    If conversation_id is provided, loads it (and enforces ownership).
    Otherwise creates a new conversation.
    """
    if conversation_id is not None:
        res = await db.execute(
            select(ConversationModel).where(
                ConversationModel.id == conversation_id,
                ConversationModel.user_id == user_id,
            )
        )
        convo = res.scalar_one_or_none()
        if convo is None:
            raise ValueError("Conversation not found")
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
    await db.flush()
    return msg


async def get_recent_messages(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 20,
) -> list[ChatMessageModel]:
    """
    Return last N messages (in chronological order).
    """
    res = await db.execute(
        select(ChatMessageModel)
        .where(ChatMessageModel.conversation_id == conversation_id)
        .order_by(desc(ChatMessageModel.id))
        .limit(limit)
    )
    rows = list(res.scalars().all())
    rows.reverse()
    return rows


async def maybe_set_title_from_first_user_message(
    db: AsyncSession,
    convo: ConversationModel,
    user_text: str,
) -> None:
    """
    If convo is still 'New chat', set title from first user message.
    """
    if convo.title != "New chat":
        return
    title = user_text.strip().splitlines()[0][:60].strip()
    if title:
        convo.title = title


async def touch_conversation(db: AsyncSession, convo: ConversationModel) -> None:
    """
    Ensure updated_at changes even if DB doesn't update on relationship changes.
    """
    convo.title = convo.title  # no-op assignment still marks dirty sometimes
    # If your updated_at doesn't change, you can also do:
    # from sqlalchemy.sql import func
    # convo.updated_at = func.now()