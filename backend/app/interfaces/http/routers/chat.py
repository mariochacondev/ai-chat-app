import asyncio
import json
import httpx
from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.rag import build_context
from app.core.utils import get_db
from app.deps import get_user_id_from_token
from app.infrastructure.chat_history import (
    get_or_create_conversation,
    add_message,
    get_recent_messages,
)
from app.application.conversations.service import (
    get_or_create_conversation,
    add_message,
    get_recent_messages,
    maybe_set_title_from_first_user_message,
    touch_conversation,
)
from app.infrastructure.db import SessionLocal
from app.infrastructure.security.auth import get_user_id_from_raw_token
from app.infrastructure.services.ollama_chat import OllamaChat
from app.infrastructure.vectorstore.qdrant_store import QdrantStore

router = APIRouter(prefix="/chat", tags=["chat"])

llm = OllamaChat()
store = QdrantStore()


def system_prompt_with_context(context: str) -> str:
    base = "You are a helpful AI assistant."
    if not context:
        return base
    return (
            base
            + "\n\nUse the following context if it is relevant. "
              "If the context is not relevant, ignore it.\n\n"
            + context
    )


@router.post("/completions")
async def chat_completion(
    prompt: str,
    conversation_id: int | None = None,
    user_id: int = Depends(get_user_id_from_token),
    db: AsyncSession = Depends(get_db),
):
    prompt = (prompt or "").strip()
    if not prompt:
        return {"role": "assistant", "content": "", "conversation_id": conversation_id}

    # 1) get/create conversation (enforce ownership)
    try:
        convo = await get_or_create_conversation(db, user_id=user_id, conversation_id=conversation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2) save user message
    await add_message(db, conversation_id=convo.id, role="user", content=prompt)
    await maybe_set_title_from_first_user_message(db, convo, prompt)

    # 3) build RAG context (degrade gracefully if it fails)
    try:
        rag_context = await build_context(llm=llm, store=store, db=db, user_id=user_id, query=prompt, k=5)
    except Exception:
        rag_context = ""

    # 4) gather recent conversation memory (includes the prompt you just saved)
    recent = await get_recent_messages(db, conversation_id=convo.id, limit=20)

    # 5) build messages for LLM (system prompt includes context)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt_with_context(rag_context)},
    ]
    for m in recent:
        if m.role in ("user", "assistant"):
            messages.append({"role": m.role, "content": m.content})

    # 6) call LLM
    content = await llm.complete(messages)

    # 7) save assistant message + touch + commit
    await add_message(db, conversation_id=convo.id, role="assistant", content=content)
    await touch_conversation(db, convo)
    await db.commit()

    return {"role": "assistant", "content": content, "conversation_id": convo.id}


@router.websocket("/ws")
async def chat_ws(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=1008, reason="Missing token")
        return

    try:
        user_id = int(get_user_id_from_raw_token(token))
    except Exception:
        await ws.close(code=1008, reason="Invalid token")
        return

    await ws.accept()

    cancel_events: dict[str, asyncio.Event] = {}
    tasks: dict[str, asyncio.Task] = {}

    async def run_stream(request_id: str, prompt: str, conversation_id: int | None):
        cancel_event = cancel_events[request_id]

        # ✅ New DB session per request (safe w/ long-lived websockets)
        async with SessionLocal() as db:
            try:
                convo = await get_or_create_conversation(db, user_id, conversation_id)

                # Save user message
                await add_message(db, convo.id, "user", prompt)
                await maybe_set_title_from_first_user_message(db, convo, prompt)

                # Build RAG context (needs db too)
                context = await build_context(llm, store, db=db, user_id=user_id, query=prompt, k=5)

                # Pull recent conversation history
                history = await get_recent_messages(db, convo.id, limit=20)

                # Build messages for LLM: system + context + history
                messages = [{"role": "system", "content": system_prompt_with_context(context)}]
                for m in history:
                    # keep it simple: only user/assistant
                    if m.role in ("user", "assistant"):
                        messages.append({"role": m.role, "content": m.content})

                # Tell client which conversation is active (important if convo created implicitly)
                await ws.send_text(json.dumps({
                    "type": "start",
                    "request_id": request_id,
                    "conversation_id": convo.id,
                }))

                # Stream assistant reply + accumulate text
                assistant_text_parts: list[str] = []
                async for chunk in llm.stream_messages(messages):
                    if cancel_event.is_set():
                        await ws.send_text(json.dumps({"type": "stopped", "request_id": request_id, "conversation_id": convo.id}))
                        # Optionally store partial assistant message on stop:
                        # if assistant_text_parts:
                        #   await add_message(db, convo.id, "assistant", "".join(assistant_text_parts))
                        #   await touch_conversation(db, convo)
                        #   await db.commit()
                        return

                    assistant_text_parts.append(chunk)
                    await ws.send_text(json.dumps({
                        "type": "delta",
                        "request_id": request_id,
                        "conversation_id": convo.id,
                        "content": chunk,
                    }))

                assistant_text = "".join(assistant_text_parts).strip()
                if assistant_text:
                    await add_message(db, convo.id, "assistant", assistant_text)

                await touch_conversation(db, convo)
                await db.commit()

                await ws.send_text(json.dumps({
                    "type": "done",
                    "request_id": request_id,
                    "conversation_id": convo.id,
                }))

            except httpx.ConnectError:
                await ws.send_text(json.dumps({
                    "type": "error",
                    "request_id": request_id,
                    "message": "LLM service unavailable (Ollama not reachable)",
                }))
            except Exception as e:
                # You can log e here
                await ws.send_text(json.dumps({
                    "type": "error",
                    "request_id": request_id,
                    "message": str(e),
                }))

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)

            msg_type = data.get("type")

            if msg_type == "prompt":
                request_id = data.get("request_id")
                prompt = (data.get("prompt") or "").strip()
                conversation_id = data.get("conversation_id")  # may be null

                if not request_id or not prompt:
                    await ws.send_text(json.dumps({"type": "error", "message": "Missing request_id/prompt"}))
                    continue

                cancel_events[request_id] = asyncio.Event()
                tasks[request_id] = asyncio.create_task(run_stream(request_id, prompt, conversation_id))

            elif msg_type == "stop":
                request_id = data.get("request_id")
                if request_id and request_id in cancel_events:
                    cancel_events[request_id].set()

            else:
                await ws.send_text(json.dumps({"type": "error", "message": "Unknown message type"}))

    except WebSocketDisconnect:
        for ev in cancel_events.values():
            ev.set()
        for t in tasks.values():
            t.cancel()
