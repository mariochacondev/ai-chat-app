import uuid
import hashlib
import io
from pypdf import PdfReader
from docx import Document
from app.infrastructure.db import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if chunk_size <= 0:
        return [text]
    if overlap < 0:
        overlap = 0
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def make_point_id(user_id: int, doc_id: str, idx: int, chunk: str) -> str:
    key = f"{user_id}:{doc_id}:{idx}:{hashlib.sha1(chunk.encode('utf-8')).hexdigest()}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)

def extract_text_from_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text)


def extract_text_from_plain(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore")

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session