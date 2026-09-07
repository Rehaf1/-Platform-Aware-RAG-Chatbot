from typing import List

from app.retrieval.retriever import RetrievalResult, RetrievedChunk

from app.generation.language_detection import detect_language

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
    """
    Lightweight word-overlap check as a hallucination guard. This only
    works when the answer and the evidence share a script/language --
    an Arabic answer grounded in English evidence (or vice versa) will
    have near-zero literal word overlap even when perfectly grounded,
    since the words themselves don't share characters. When the answer's
    detected language differs from the evidence's, this check is skipped
    entirely and grounding is trusted to retrieval + the prompt
    constraints instead (Section 26's cross-language requirement depends
    on exactly this: an Arabic question must be answerable from
    English-only source text).
    """
    if not chunks or not answer_text.strip():
        return False

    evidence_text = " ".join(c.text for c in chunks)
    answer_language = detect_language(answer_text)
    evidence_language = detect_language(evidence_text)

    if answer_language != evidence_language:
        return True

    evidence_words = {
        w for w in evidence_text.lower().split() if len(w) > 3
    }
    answer_words = {w for w in answer_text.lower().split() if len(w) > 3}
    if not answer_words:
        return False

    overlap_ratio = len(answer_words & evidence_words) / len(answer_words)
    return overlap_ratio >= 0.15  # generous starting threshold; tune against eval set