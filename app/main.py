from dotenv import load_dotenv
load_dotenv(".env")
import time
from fastapi import FastAPI, Depends, HTTPException
from app.api.documents import router as documents_router
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.auth.jwt_auth import get_trusted_context, TrustedContext
from app.generation.orchestrator import generate_answer
from app.generation.query_preprocessing import preprocess_query

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
) -> ChatResponse:
    """
    ctx يجي من التوكن الموثوق (JWT) تلقائياً.
    """
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

    return ChatResponse(**result)