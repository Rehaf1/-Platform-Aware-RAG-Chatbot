from typing import List, Dict, Any

from app.retrieval.retriever import RetrievedChunk

""""
def build_citations(chunks: List[RetrievedChunk]) -> List[Dict[str, Any]]:
    citations: List[Dict[str, Any]] = []
    seen = set()
    for chunk in chunks:
        #key = (chunk.document_name, chunk.chunk_index)
        key = (chunk.document_name, chunk.text.strip())
        


        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "document_name": chunk.document_name,
                "document_version": chunk.version,
                "page": None,     # need to wire once ingestion stores page numbers
                "section": chunk.section,  
                "excerpt": chunk.text[:400],
            }
        )
    return citations
"""
def build_citations(chunks: List[RetrievedChunk]) -> List[Dict[str, Any]]:
    """
    One citation per unique source chunk actually used as evidence.

    Chunking with overlap means one chunk's text can be entirely
    contained within another (e.g. chunk N is the tail end of chunk
    N-1's text plus a bit more) -- a plain equality check doesn't catch
    that, since the texts aren't identical, just one is a prefix/subset
    of the other. This keeps only the longer chunk when one fully
    contains another, since showing both as "different sources" would
    just repeat the same underlying passage twice.
    """
    # Sort longest-first so we always keep the more complete version
    # when a shorter chunk turns out to be contained in a longer one.
    sorted_chunks = sorted(chunks, key=lambda c: len(c.text), reverse=True)

    kept: List[RetrievedChunk] = []
    for chunk in sorted_chunks:
        text = chunk.text.strip()
        if any(text in already.text for already in kept):
            continue
        kept.append(chunk)

    citations: List[Dict[str, Any]] = []
    for chunk in kept:
        citations.append(
            {
                "document_name": chunk.document_name,
                "document_version": chunk.version,
                "page": None,           # TODO: wire once ingestion tracks page numbers
                "section": chunk.section,
                "excerpt": chunk.text[:400],
            }
        )
    return citations