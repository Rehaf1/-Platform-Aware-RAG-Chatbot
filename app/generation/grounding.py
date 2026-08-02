from typing import List

from app.retrieval.retriever import RetrievalResult, RetrievedChunk


FALLBACK_EN = (
    "The approved documentation does not contain enough information to "
    "answer this question. Please rephrase, or contact support if you "
    "believe this platform should have this information."
)
FALLBACK_AR = (
    "لا تحتوي الوثائق المعتمدة على معلومات كافية للإجابة على هذا السؤال. "
    "يرجى إعادة صياغة السؤال، أو التواصل مع الدعم إذا كنت تعتقد أن هذه "
    "المنصة يجب أن تحتوي على هذه المعلومة."
)


def controlled_fallback(language: str) -> str:
    return FALLBACK_AR if language == "ar" else FALLBACK_EN


def should_fallback(retrieval_result: RetrievalResult) -> bool:
    return not retrieval_result.grounded or len(retrieval_result.chunks) == 0


def validate_answer_is_grounded(answer_text: str, chunks: List[RetrievedChunk]) -> bool:
    if not chunks or not answer_text.strip():
        return False

    evidence_words = {
        w for w in " ".join(c.text for c in chunks).lower().split() if len(w) > 3
    }
    answer_words = {w for w in answer_text.lower().split() if len(w) > 3}
    if not answer_words:
        return False

    overlap_ratio = len(answer_words & evidence_words) / len(answer_words)
    return overlap_ratio >= 0.15  # generous starting threshold; tune against eval set
