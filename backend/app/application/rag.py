from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.services.ollama_chat import OllamaChat
from app.infrastructure.vectorstore.qdrant_store import QdrantStore
from app.infrastructure.models import DocChunkModel


async def build_context(
    llm: OllamaChat,
    store: QdrantStore,
    db: AsyncSession,
    user_id: int,
    query: str,
    k: int = 5,
) -> str:
    query = query.strip()
    if not query:
        return ""

    qvec = await llm.embed(query)
    store.ensure_collection(vector_size=len(qvec))

    hits = store.search(qvec, limit=k, user_id=user_id)
    if not hits:
        return ""

    # Qdrant point ids => chunk_ids (ints)
    chunk_ids: list[int] = []
    for h in hits:
        try:
            chunk_ids.append(int(h.id))
        except Exception:
            continue

    if not chunk_ids:
        return ""

    res = await db.execute(select(DocChunkModel).where(DocChunkModel.id.in_(chunk_ids)))
    rows = res.scalars().all()
    by_id = {r.id: r for r in rows}

    ordered: list[str] = []
    for cid in chunk_ids:
        r = by_id.get(cid)
        if r and r.text and r.text.strip():
            ordered.append(r.text.strip())

    if not ordered:
        return ""

    return "\n\n---\n\n".join(ordered)
