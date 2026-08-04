
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status as http_status
from app.auth.authorization import require_admin
from app.auth.jwt_auth import TrustedContext
from app.ingestion.collection_and_validation import validate_document
from app.ingestion.loader import load_document_text
from app.ingestion.cleaning import clean_text
from app.ingestion.chunking import chunk_text_structural_aware
from app.ingestion.metadata import build_chunks_with_metadata


from app.ingestion.duplicate_detection import (
    hash_text, load_registry, save_registry, is_duplicate, normalize_for_hashing,
)
from app.retrieval.vector_store import add_chunks_to_store, collection
router = APIRouter()
REGISTRY_PATH = "ingested_documents.json"



@router.post("/documents/upload")
def upload_document(
    file: UploadFile = File(...),
    module: str = Form(None),
    access_level: str = Form(None),
    roles: str = Form(None),
    version: str = Form("1.0"),
    ctx: TrustedContext = Depends(require_admin),
):
    platform_dir = Path("sample_data") / ctx.platform_id
    platform_dir.mkdir(parents=True, exist_ok=True)

    save_path = platform_dir / file.filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Step 1: validate (existence/type/size)
    is_valid, reason = validate_document(str(save_path))
    if not is_valid:
        save_path.unlink()  # clean up the bad file we just wrote
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=reason)

    # Step 2: load + clean
    raw_text = load_document_text(str(save_path))
    cleaned_text = clean_text(raw_text)

    # Step 3: duplicate check
    registry = load_registry(REGISTRY_PATH)
    text_hash = hash_text(normalize_for_hashing(cleaned_text))
    if is_duplicate(text_hash, registry):
        save_path.unlink()
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Duplicate content already ingested")
    registry[text_hash] = {"document_name": file.filename}
    save_registry(registry, REGISTRY_PATH)

    # Step 4: chunk + tag + store
    structured_chunks = chunk_text_structural_aware(cleaned_text)
    chunk_strings = [c for _, c in structured_chunks]
    sections = [s for s, _ in structured_chunks]

    tagged_chunks = build_chunks_with_metadata(
        chunk_strings=chunk_strings,
        filepath=str(save_path),
        sections=sections,
        tenant_id=ctx.tenant_id,
        module=module,
        access_level=access_level,
        roles=roles.split(",") if roles else [],
        version=version,
    )
    add_chunks_to_store(tagged_chunks)

    return {
        "document_name": file.filename,
        "platform_id": ctx.platform_id,
        "chunks_stored": len(tagged_chunks),
        "collection_count": collection.count(),
    }