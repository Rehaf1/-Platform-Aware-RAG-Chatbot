"""
Arabic similarity-threshold sweep (D-018 follow-up).

Cross-lingual retrieval (an Arabic question against English-only source
documents) systematically scores lower on cosine similarity than
same-language retrieval, even when the match is semantically correct --
the embedding model's cross-lingual alignment isn't as tight as its
within-language alignment. DEFAULT_SIMILARITY_THRESHOLD (0.35) was
tuned informally against English questions; this script checks whether
that same cutoff is too strict for Arabic questions, which would show
up as correct-but-rejected retrievals (silently degrading to a
"no evidence" fallback for a question that actually had a good match).

This does NOT call the LLM -- it only measures retrieval scores, so it
is fast and free to re-run.

Usage:
    PYTHONPATH=. python scripts/arabic_threshold_sweep.py
"""

from dotenv import load_dotenv
load_dotenv(".env")

from app.retrieval.retriever import retrieve

# A handful of Arabic questions with a known-correct English-language
# answer somewhere in the IMTITHAL sample_data. Replace/extend this list
# with real Arabic questions from your own benchmark_subset.json if you
# have a larger labeled set -- more questions make the sweep more
# trustworthy than these five.
ARABIC_TEST_QUESTIONS = [
    "كيف أعين مسؤول رقابة؟",
    "ما هو الدور المطلوب لتعيين مسؤول رقابة؟",
    "كم مرة يجب مراجعة الضوابط؟",
    "من يستطيع إعادة تعيين مسؤول الرقابة؟",
    "ماذا يحدث بعد تعيين مسؤول رقابة جديد؟",
]

CANDIDATE_THRESHOLDS = [0.35, 0.30, 0.25, 0.20, 0.15]

PLATFORM_ID = "imtithal"
TENANT_ID = "demo_tenant"


def main():
    print(f"{'Threshold':<10} {'Question':<45} {'Top score':<10} {'Would pass?'}")
    print("-" * 90)

    results_by_threshold = {t: {"pass": 0, "total": 0} for t in CANDIDATE_THRESHOLDS}

    for question in ARABIC_TEST_QUESTIONS:
        # similarity_threshold=0.0 means "don't filter" -- we want the raw
        # top score for this question regardless of any cutoff, then check
        # it against each candidate threshold ourselves below.
        result = retrieve(
            question,
            platform_id=PLATFORM_ID,
            tenant_id=TENANT_ID,
            similarity_threshold=0.0,
        )
        top_score = max((c.score for c in result.chunks), default=0.0)

        for threshold in CANDIDATE_THRESHOLDS:
            passes = top_score >= threshold
            results_by_threshold[threshold]["total"] += 1
            if passes:
                results_by_threshold[threshold]["pass"] += 1
            print(f"{threshold:<10} {question[:43]:<45} {top_score:<10.3f} {'YES' if passes else 'no'}")
        print()

    print("=" * 90)
    print("SUMMARY -- pass rate per candidate threshold")
    print("=" * 90)
    for threshold, counts in results_by_threshold.items():
        rate = counts["pass"] / counts["total"] if counts["total"] else 0
        print(f"  threshold={threshold:<6} pass_rate={rate:.0%} ({counts['pass']}/{counts['total']})")

    print("\nLower the threshold until the pass rate stops improving -- that")
    print("point is your recommended ARABIC_SIMILARITY_THRESHOLD. Going lower")
    print("than that risks admitting genuinely irrelevant matches as evidence.")


if __name__ == "__main__":
    main()
