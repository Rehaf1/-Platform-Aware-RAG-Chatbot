from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from app.retrieval.vector_store import collection
from app.ingestion.embeddings import embed_texts


DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.35   # cosine similarity, range -1..1
CANDIDATE_MULTIPLIER = 4              # over-fetch factor before post-filtering
VERSION_MATCH_BOOST = 0.05


@dataclass
class RetrievedChunk:
    text: str
    document_name: str
    platform_id: str
    tenant_id: str
    module: Optional[str]
    language: Optional[str]
    version: Optional[str]
    access_level: Optional[str]
    roles: List[str]
    chunk_index: int
    section: Optional[str]
    source_path: str
    score: float  # cosine similarity after any version boost, higher = better


@dataclass
class RetrievalResult:
    chunks: List[RetrievedChunk] = field(default_factory=list)
    grounded: bool = False          # False -> caller MUST use the controlled fallback
    reason: Optional[str] = None    # populated when grounded is False


def _l2_distance_to_cosine_similarity(distance: float) -> float:
    cos_sim = 1 - (distance / 2)
    return max(-1.0, min(1.0, cos_sim))


def _role_permitted(chunk_roles_str: str, user_role: Optional[str]) -> bool:
    if not chunk_roles_str:
        return True
    if user_role is None:
        return False
    allowed = {r.strip() for r in chunk_roles_str.split(",") if r.strip()}
    return user_role in allowed


def retrieve(
    query: str,
    *,
    platform_id: str,
    tenant_id: str,
    module: Optional[str] = None,
    user_role: Optional[str] = None,
    product_version: Optional[str] = None,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> RetrievalResult:
    
    if not platform_id or not tenant_id:
        raise ValueError(
            "platform_id and tenant_id are required and must come from "
            "trusted request context, never from the raw user message."
        )

    query_embedding = embed_texts([query])[0]

    where_conditions: List[Dict[str, Any]] = [
        {"platform_id": platform_id},
        {"tenant_id": tenant_id},
    ]
    if module:
        where_conditions.append({"module": module})
    where_clause = {"$and": where_conditions} if len(where_conditions) > 1 else where_conditions[0]

    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(top_k * CANDIDATE_MULTIPLIER, top_k),
        where=where_clause,
    )

    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    candidates: List[RetrievedChunk] = []
    for doc_text, meta, distance in zip(documents, metadatas, distances):
        if not _role_permitted(meta.get("roles", ""), user_role):
            continue

        score = _l2_distance_to_cosine_similarity(distance)
        if product_version and meta.get("version") == product_version:
            score += VERSION_MATCH_BOOST

        if score < similarity_threshold:
            continue

        candidates.append(
            RetrievedChunk(
                text=doc_text,
                document_name=meta.get("document_name", ""),
                platform_id=meta.get("platform_id", ""),
                tenant_id=meta.get("tenant_id", ""),
                module=meta.get("module") or None,
                language=meta.get("language") or None,
                version=meta.get("version") or None,
                access_level=meta.get("access_level") or None,
                roles=[r for r in meta.get("roles", "").split(",") if r],
                chunk_index=meta.get("chunk_index", -1),
                section=meta.get("section") or None,
                source_path=meta.get("source_path", ""),
                score=score,
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    top_chunks = candidates[:top_k]

    if not top_chunks:
        return RetrievalResult(chunks=[], grounded=False, reason="insufficient_evidence")

    return RetrievalResult(chunks=top_chunks, grounded=True)
