
from app.retrieval.retriever import retrieve
from app.generation.prompts import build_messages
from app.generation.citation import build_citations
from app.generation.grounding import should_fallback, controlled_fallback


def ask(question: str, *, platform_id: str, tenant_id: str, language: str = "en", user_role=None):
    result = retrieve(
        question,
        platform_id=platform_id,
        tenant_id=tenant_id,
        user_role=user_role,
    )

    print(f"\n--- Q: {question!r} (platform={platform_id}, tenant={tenant_id}) ---")

    if should_fallback(result):
        print("FALLBACK:", controlled_fallback(language))
        return

    messages = build_messages(
        question=question,
        chunks=result.chunks,
        platform_name=platform_id,
        tenant_id=tenant_id,
        module=None,
        user_role=user_role,
        language=language,
    )
    citations = build_citations(result.chunks)

    print("Retrieved", len(result.chunks), "chunk(s), top score:", round(result.chunks[0].score, 3))
    print("System prompt (first 120 chars):", messages[0]["content"][:120].replace("\n", " "), "...")
    print("Citations:", citations)
    # messages would go to the LLM here (LLM call is a separate,
    # swappable-provider concern — not this module's job).


if __name__ == "__main__":
    # Matches the tagged chunk written by scripts/test_pipeline.py
    ask("What is this document about?", platform_id="imtithal", tenant_id="demo_tenant")

    # TC-03 style: same question, wrong platform -> must fall back
    ask("What is this document about?", platform_id="emdad", tenant_id="demo_tenant")

    # TC-04 style: unrelated question -> must fall back
    ask("How do I file a tax return in Germany?", platform_id="imtithal", tenant_id="demo_tenant")
