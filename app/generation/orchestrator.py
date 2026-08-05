from typing import Optional, List, Dict, Any

from app.retrieval.retriever import retrieve
from app.generation.prompts import build_messages
from app.generation.citations import build_citations
from app.generation.grounding import (
    should_fallback,
    controlled_fallback,
    validate_answer_is_grounded,
)
from app.generation.llm_client import call_llm
from app.generation.unanswered_log import log_unanswered_question

def generate_answer(
    question: str,
    *,
    platform_id: str,
    tenant_id: str,
    platform_name: Optional[str] = None,
    module: Optional[str] = None,
    user_role: Optional[str] = None,
    language: str = "en",
    product_version: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    platform_id / tenant_id / user_role: trusted context — يجب أن تأتي
    من التوكن الموثوق (JWT)، لا من نص السؤال أبداً.
    """
    retrieval_result = retrieve(
        question,
        platform_id=platform_id,
        tenant_id=tenant_id,
        module=module,
        user_role=user_role,
        product_version=product_version,
    )

    if should_fallback(retrieval_result):
        log_unanswered_question(question, platform_id, tenant_id)
        return {
            "answer": controlled_fallback(language),
            "citations": [],
            "grounded": False,
            "fallback_used": True,
        }

    messages = build_messages(
        question=question,
        chunks=retrieval_result.chunks,
        platform_name=platform_name or platform_id,
        tenant_id=tenant_id,
        module=module,
        user_role=user_role,
        language=language,
        conversation_history=conversation_history,
    )

    answer_text = call_llm(messages)
    citations = build_citations(retrieval_result.chunks)

    if not validate_answer_is_grounded(answer_text, retrieval_result.chunks):
        return {
            "answer": controlled_fallback(language),
            "citations": [],
            "grounded": False,
            "fallback_used": True,
        }

    return {
        "answer": answer_text,
        "citations": citations,
        "grounded": True,
        "fallback_used": False,
    }