"""
Runs every question in benchmark_subset.json through the real ingestion +
retrieval + generation pipeline, scores the results, and saves both raw
per-question output and aggregate metrics.

Each question gets its own isolated tenant (benchmark:q_<id>), reusing the
exact same platform/tenant isolation mechanism proven in tests/test_isolation.py,
so benchmark data can never mix with real IMTITHAL/EMDAD content.

No Docker/Postgres needed -- only Chroma (local) and a real GROQ_API_KEY.
"""

import json
import re
import time
from dotenv import load_dotenv

load_dotenv(".env")

from app.ingestion.chunking import chunk_text_recursive
from app.ingestion.metadata import build_chunks_with_metadata
from app.retrieval.vector_store import add_chunks_to_store, collection
from app.retrieval.retriever import retrieve
from app.generation.orchestrator import generate_answer

PLATFORM_ID = "benchmark"
TOP_K = 5


def normalize(text: str) -> str:
    """Lowercase + collapse whitespace, for loose substring matching."""
    return re.sub(r"\s+", " ", text.strip().lower())


def ingest_question_passages(question_id: str, passages: list) -> str:
    """
    Chunks and stores one question's passages under an isolated tenant.
    Returns the tenant_id used, so the caller can query and clean up.
    """
    tenant_id = f"q_{question_id}"
    combined_text = "\n\n".join(p["text"] for p in passages)

    chunks = chunk_text_recursive(combined_text, chunk_size=80, overlap=15)

    fake_filepath = f"sample_data/{PLATFORM_ID}/{question_id}.txt"
    tagged_chunks = build_chunks_with_metadata(
        chunk_strings=chunks,
        filepath=fake_filepath,
        tenant_id=tenant_id,
        version="benchmark",
    )
    add_chunks_to_store(tagged_chunks)
    return tenant_id


def cleanup_tenant(tenant_id: str) -> None:
    collection.delete(where={"$and": [{"platform_id": PLATFORM_ID}, {"tenant_id": tenant_id}]})


def evaluate_question(item: dict, source: str) -> dict:
    question_id = item["id"]
    question = item["question"]
    gold_answer = normalize(item["gold_answer"])
    language = item["language"]

    tenant_id = ingest_question_passages(question_id, item["passages"])

    result = {
        "id": question_id,
        "source": source,
        "language": language,
        "question": question,
        "gold_answer": item["gold_answer"],
    }

    try:
        # --- retrieval metrics ---
        retrieval_result = retrieve(
            question,
            platform_id=PLATFORM_ID,
            tenant_id=tenant_id,
            top_k=TOP_K,
            similarity_threshold=0.0,  # bypass fallback here; we want raw ranking
        )

        hit_rank = None
        for rank, chunk in enumerate(retrieval_result.chunks, start=1):
            if gold_answer and gold_answer in normalize(chunk.text):
                hit_rank = rank
                break

        result["retrieval_hit_rank"] = hit_rank
        result["retrieval_recall_at_k"] = hit_rank is not None
        result["retrieval_mrr"] = (1.0 / hit_rank) if hit_rank else 0.0

        # --- generation metrics ---
        gen = generate_answer(
            question,
            platform_id=PLATFORM_ID,
            tenant_id=tenant_id,
            language=language,
        )
        result["generated_answer"] = gen["answer"]
        result["grounded"] = gen["grounded"]
        result["fallback_used"] = gen["fallback_used"]
        result["generation_correct"] = bool(gold_answer) and gold_answer in normalize(gen["answer"])

    finally:
        cleanup_tenant(tenant_id)

    return result


def main():
    with open("benchmark_subset.json", encoding="utf-8") as f:
        data = json.load(f)

    all_items = (
        [(item, "hotpotqa_en") for item in data["hotpotqa_en"]]
        + [(item, "tydiqa") for item in data["tydiqa"]]
    )

    print(f"Running evaluation on {len(all_items)} questions...\n")

    results = []
    for i, (item, source) in enumerate(all_items, start=1):
        print(f"[{i}/{len(all_items)}] {source} :: {item['id']}")
        try:
            r = evaluate_question(item, source)
            results.append(r)
        except Exception as exc:
            print(f"  FAILED: {exc}")
            results.append({"id": item["id"], "source": source, "error": str(exc)})
        time.sleep(0.3)  # small pause, be gentle on the Groq free tier rate limit

    # --- aggregate metrics ---
    valid = [r for r in results if "error" not in r]
    n = len(valid)
    recall_at_k = sum(1 for r in valid if r["retrieval_recall_at_k"]) / n if n else 0
    mrr = sum(r["retrieval_mrr"] for r in valid) / n if n else 0
    gen_accuracy = sum(1 for r in valid if r["generation_correct"]) / n if n else 0
    fallback_rate = sum(1 for r in valid if r["fallback_used"]) / n if n else 0

    summary = {
        "total_questions": len(all_items),
        "successful_runs": n,
        "failed_runs": len(results) - n,
        "recall_at_k": round(recall_at_k, 3),
        "mrr": round(mrr, 3),
        "generation_accuracy": round(gen_accuracy, 3),
        "fallback_rate": round(fallback_rate, 3),
    }

    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "per_question": results}, f, ensure_ascii=False, indent=2)

    print("\n=== SUMMARY ===")
    for k, v in summary.items():
        print(f"{k}: {v}")
    print("\nFull results saved to benchmark_results.json")


if __name__ == "__main__":
    main()
