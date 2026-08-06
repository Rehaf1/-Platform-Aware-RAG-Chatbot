from dotenv import load_dotenv
load_dotenv(".env")

import time

from fastapi import FastAPI, Depends, HTTPException
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
    add_message,
    add_citations,
    log_audit_event,
)

app = FastAPI(title="APTWatch Platform-Aware RAG Chatbot", version="0.1.0")
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


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    module: Optional[str] = None
    language: str = "en"
    product_version: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    grounded: bool
    fallback_used: bool


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

    result = generate_answer(
        clean_question,
        platform_id=ctx.platform_id,
        tenant_id=ctx.tenant_id,
        module=request.module,
        user_role=ctx.user_role,
        language=request.language,
        product_version=request.product_version,
        conversation_history=request.conversation_history,
    )

    latency_ms = (time.perf_counter() - start) * 1000

    # --- persist to PostgreSQL ---
    # A failure here should never break the chat response itself — the
    # answer already succeeded from the user's point of view. Isolate
    # persistence errors so a DB hiccup doesn't turn a good answer into
    # a 500.
    try:
        platform_row = get_or_create_platform(db, ctx.platform_id)
        tenant_row = get_or_create_tenant(db, platform_row, ctx.tenant_id)
        user_row = get_or_create_user(db, platform_row, tenant_row, ctx.user_id, ctx.user_role)

        conversation = create_conversation(
            db, user_row, platform_row, tenant_row, title=clean_question[:100]
        )
        add_message(db, conversation, role="user", content=clean_question)
        assistant_message = add_message(
            db,
            conversation,
            role="assistant",
            content=result["answer"],
            grounded=result["grounded"],
            fallback_used=result["fallback_used"],
        )
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
    except Exception as exc:  # noqa: BLE001 — persistence is best-effort here
        print(f"[warning] failed to persist chat to database: {exc}")

    # Keep the existing stdout/JSON log too — cheap, and useful when the
    # DB itself is the thing having trouble.
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

    return ChatResponse(**result)