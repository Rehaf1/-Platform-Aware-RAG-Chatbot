from typing import List, Dict, Any

from app.retrieval.retriever import RetrievedChunk


def build_citations(chunks: List[RetrievedChunk]) -> List[Dict[str, Any]]:
    citations: List[Dict[str, Any]] = []
    seen = set()
    for chunk in chunks:
        key = (chunk.document_name, chunk.chunk_index)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "document_name": chunk.document_name,
                "document_version": chunk.version,
                "page": None,     # need to wire once ingestion stores page numbers
                "section": None,  # need to wire once ingestion stores section headers
                "excerpt": chunk.text[:280],
            }
        )
    return citations
