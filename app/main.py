from dotenv import load_dotenv
load_dotenv(".env")

import time

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.api.documents import router as documents_router
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.auth.jwt_auth import get_trusted_context, TrustedContext
from app.generation.orchestrator import generate_answer
from app.generation.query_preprocessing import preprocess_query
from app.api.audit_log import log_chat_request
from app.db.database import get_db
from app.db.crud import (
    get_or_create_platform,
    get_or_create_tenant,
    get_or_create_user,
    create_conversation,
    get_conversation_for_user,
    get_recent_messages,
    add_message,
    add_citations,
    get_message_for_user,
    add_feedback,
    log_audit_event,
)

app = FastAPI(title="APTWatch Platform-Aware RAG Chatbot", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health")
def health() -> Dict[str, str]:
    """Liveness probe — process is up."""
    return {"status": "ok"}


@app.get("/ready")
def ready() -> Dict[str, str]:
    """Readiness probe — confirms Chroma is reachable."""
    try:
        from app.retrieval.vector_store import collection
        collection.count()
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Not ready: {exc}")


# ---------------------------------------------------------------------------
# /api/v1/chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    module: Optional[str] = None
    language: str = "en"
    product_version: Optional[str] = None
    conversation_id: Optional[str] = None
    # Conversation continuity, per the agreed design: the CLIENT decides
    # whether this is a follow-up (send the conversation_id it got back
    # last time) or a fresh start (omit it) -- the server never guesses
    # based on elapsed time. An unknown/foreign ID is treated the same as
    # omitting it: a new conversation starts rather than erroring out.


class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    grounded: bool
    fallback_used: bool
    conversation_id: str
    # Always returned -- the client stores this and sends it back on the
    # next message in the same conversation.
    message_id: Optional[str] = None
    # The assistant message's DB row id, so the client can attach
    # feedback (POST /api/v1/feedback) to this exact answer. None if
    # persistence failed (see the try/except below) -- the client should
    # hide the feedback buttons for that message in that rare case.


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    ctx: TrustedContext = Depends(get_trusted_context),
    db: Session = Depends(get_db),
) -> ChatResponse:
    start = time.perf_counter()

    try:
        clean_question = preprocess_query(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # --- resolve identity + conversation (best-effort; see try/except below) ---
    conversation = None
    user_row = None
    history_for_prompt = None

    try:
        platform_row = get_or_create_platform(db, ctx.platform_id)
        tenant_row = get_or_create_tenant(db, platform_row, ctx.tenant_id)
        user_row = get_or_create_user(db, platform_row, tenant_row, ctx.user_id, ctx.user_role)

        if request.conversation_id:
            conversation = get_conversation_for_user(db, request.conversation_id, user_row)

        if conversation is not None:
            # continuing an existing conversation -- pull recent turns as
            # context for the LLM, in the {"role", "content"} shape
            # prompts.build_messages() already expects
            prior_messages = get_recent_messages(db, conversation, limit=10)
            history_for_prompt = [
                {"role": m.role, "content": m.content} for m in prior_messages
            ]
        else:
            conversation = create_conversation(
                db, user_row, platform_row, tenant_row, title=clean_question[:100]
            )
    except Exception as exc:  # noqa: BLE001 -- DB issues must not block answering
        print(f"[warning] failed to resolve conversation from database: {exc}")

    result = generate_answer(
        clean_question,
        platform_id=ctx.platform_id,
        tenant_id=ctx.tenant_id,
        module=request.module,
        user_role=ctx.user_role,
        language=request.language,
        product_version=request.product_version,
        conversation_history=history_for_prompt,
    )

    latency_ms = (time.perf_counter() - start) * 1000

    # --- persist to PostgreSQL (best-effort, see module docstring above) ---
    assistant_message_id = None
    try:
        if conversation is not None:
            add_message(db, conversation, role="user", content=clean_question)
            assistant_message = add_message(
                db,
                conversation,
                role="assistant",
                content=result["answer"],
                grounded=result["grounded"],
                fallback_used=result["fallback_used"],
            )
            assistant_message_id = str(assistant_message.id)
            if result["citations"]:
                add_citations(db, assistant_message, result["citations"])

        log_audit_event(
            db,
            event="chat_request",
            platform_id=ctx.platform_id,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            user_role=ctx.user_role,
            grounded=result["grounded"],
            fallback_used=result["fallback_used"],
            num_citations=len(result["citations"]),
            latency_ms=latency_ms,
        )
    except Exception as exc:  # noqa: BLE001 -- persistence is best-effort here
        print(f"[warning] failed to persist chat to database: {exc}")

    log_chat_request(
        platform_id=ctx.platform_id,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        user_role=ctx.user_role,
        grounded=result["grounded"],
        fallback_used=result["fallback_used"],
        num_citations=len(result["citations"]),
        latency_ms=latency_ms,
    )

    return ChatResponse(
        **result,
        conversation_id=str(conversation.id) if conversation is not None else "",
        message_id=assistant_message_id,
    )


# ---------------------------------------------------------------------------
# /api/v1/feedback
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    message_id: str
    is_helpful: bool
    comment: Optional[str] = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    status: str


@app.post("/api/v1/feedback", response_model=FeedbackResponse)
def feedback(
    request: FeedbackRequest,
    ctx: TrustedContext = Depends(get_trusted_context),
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """
    Attaches a thumbs up/down (+ optional comment) to a previously
    returned assistant message. Scoped to the requesting user via
    get_message_for_user -- a user can only rate messages from their own
    conversations.
    """
    platform_row = get_or_create_platform(db, ctx.platform_id)
    tenant_row = get_or_create_tenant(db, platform_row, ctx.tenant_id)
    user_row = get_or_create_user(db, platform_row, tenant_row, ctx.user_id, ctx.user_role)

    message = get_message_for_user(db, request.message_id, user_row)
    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found, or does not belong to this user.",
        )

    add_feedback(
        db,
        message,
        user_row,
        is_helpful=request.is_helpful,
        comment=request.comment,
    )
    return FeedbackResponse(status="ok")
