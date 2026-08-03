from pathlib import Path

def build_chunks_with_metadata(
    chunk_strings,
    filepath,
    sections=None,
    tenant_id="demo_tenant",
    module=None,
    language="en",
    access_level=None,
    roles=None,
    version="1.0",
):
    if roles is None:
        roles = []

    if sections is None:
        sections = [None] * len(chunk_strings)

    path = Path(filepath)
    platform_id = path.parent.name
    document_name = path.name

    chunks = []

    for chunk_index, chunk_text in enumerate(chunk_strings):
        chunks.append({
            "tenant_id": tenant_id,
            "platform_id": platform_id,
            "document_name": document_name,
            "chunk_index": chunk_index,
            "text": chunk_text,
            "module": module,
            "language": language,
            "access_level": access_level,
            "roles": roles,
            "version": version,
            "source_path": str(path),
            "section": sections[chunk_index],
        })

    return chunks