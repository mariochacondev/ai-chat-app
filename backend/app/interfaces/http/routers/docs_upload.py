from __future__ import annotations
import hashlib
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.deps import get_user_id_from_token
from app.infrastructure.services.ollama_chat import OllamaChat
from app.infrastructure.vectorstore.qdrant_store import QdrantStore
from app.infrastructure.models import DocumentModel, DocChunkModel
from app.core.utils import get_db, extract_text_from_pdf, chunk_text,extract_text_from_docx, extract_text_from_plain

router = APIRouter(prefix="/docs", tags=["docs"])

llm = OllamaChat()
store = QdrantStore()


class UploadOpts(BaseModel):
    doc_id: Optional[str] = None
    chunk_size: int = 800
    chunk_overlap: int = 100

@router.post("/upload")
async def upload_doc(
    doc_id: str | None = None,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
    file: UploadFile = File(...),
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    name = file.filename or "document"
    dtype = (file.content_type or "").lower()
    if not doc_id:
        doc_id = name

    #Extract text
    try:
        if dtype == "application/pdf" or name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(raw)
        elif dtype in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ) or name.lower().endswith(".docx"):
            text = extract_text_from_docx(raw)
        elif dtype.startswith("text/") or name.lower().endswith(".txt"):
            text = raw.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=415, detail=f"Unsupported type: {dtype or name}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        return {"ok": True, "inserted": 0, "doc_id": doc_id, "filename": name, "content_type": dtype}

    #Replace existing (same user+doc_id)
    res = await db.execute(
        select(DocumentModel).where(
            DocumentModel.user_id == user_id,
            DocumentModel.doc_id == doc_id,
        )
    )
    existing = res.scalar_one_or_none()
    if existing is not None:
        # ✅ delete vectors for that document_id in Qdrant first
        try:
            store.delete_by_document_id(user_id=user_id, document_id=existing.id)
        except Exception:
            # don't block upload if qdrant hiccups; but log in real app
            pass

        await db.delete(existing)
        await db.flush()

    #Insert document + chunks (DB first)
    doc = DocumentModel(
        user_id=user_id,
        doc_id=doc_id,
        filename=name,
        content_type=dtype or "application/octet-stream",
    )
    db.add(doc)
    await db.flush()  # doc.id available

    chunk_rows: list[DocChunkModel] = []
    for i, chunk in enumerate(chunks):
        row = DocChunkModel(
            document_id=doc.id,
            chunk_index=i,
            text=chunk,
            sha1=hashlib.sha1(chunk.encode("utf-8")).hexdigest(),
        )
        db.add(row)
        chunk_rows.append(row)

    await db.flush()
    await db.commit()

    #Embed + upsert Qdrant
    first_vec = await llm.embed(chunk_rows[0].text)
    store.ensure_collection(vector_size=len(first_vec))

    inserted = 0
    for idx, row in enumerate(chunk_rows):
        vec = first_vec if idx == 0 else await llm.embed(row.text)
        store.upsert(
            point_id=row.id,
            vector=vec,
            payload={
                "user_id": user_id,
                "document_id": doc.id,
                "doc_id": doc.doc_id,
                "chunk_index": row.chunk_index,
                "sha1": row.sha1,
                "source": doc.filename,
            },
        )
        inserted += 1

    return {
        "ok": True,
        "doc_id": doc.doc_id,
        "document_id": doc.id,
        "inserted": inserted,
        "filename": name,
        "content_type": dtype,
    }



@router.get("/list")
async def list_docs(
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(DocumentModel)
        .where(DocumentModel.user_id == user_id)
        .order_by(DocumentModel.created_at.desc())
    )
    docs = res.scalars().all()

    return {
        "ok": True,
        "docs": [
            {
                "doc_id": d.doc_id,
                "document_id": d.id,
                "filename": d.filename,
                "content_type": d.content_type,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ],
    }

@router.delete("/{doc_id}")
async def delete_doc(
    doc_id: str,
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(DocumentModel).where(
            DocumentModel.user_id == user_id,
            DocumentModel.doc_id == doc_id,
        )
    )
    doc = res.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # delete vectors
    try:
        store.delete_by_document_id(user_id=user_id, document_id=doc.id)
    except Exception:
        pass

    await db.delete(doc)
    await db.commit()

    return {"ok": True, "deleted": doc_id}
