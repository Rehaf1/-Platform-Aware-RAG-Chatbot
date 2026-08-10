
import shutil
from pathlib import Path
from collections import Counter
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status as http_status
from app.auth.authorization import require_admin
from app.auth.jwt_auth import TrustedContext
from app.ingestion.collection_and_validation import validate_document
from app.ingestion.loader import load_document_text
from app.ingestion.cleaning import clean_text
from app.ingestion.chunking import chunk_text_structural_aware
from app.ingestion.metadata import build_chunks_with_metadata
from app.ingestion.document_status import set_status, get_status, load_status_registry, save_status_registry
from app.generation.unanswered_log import get_unanswered_questions
from app.generation.unanswered_log import get_unanswered_questions
from app.ingestion.summarization import summarize_document
from app.ingestion.duplicate_detection import (
    hash_text, load_registry, save_registry, is_duplicate, normalize_for_hashing,
)
from app.retrieval.vector_store import add_chunks_to_store, collection
from app.db.database import SessionLocal
from app.db.crud import (
    get_or_create_platform,
    get_or_create_tenant,
    create_document,
    create_document_version,
    create_document_chunks,
)
router = APIRouter()
REGISTRY_PATH = "ingested_documents.json"


@router.get("/documents/{document_name}/status")
def get_document_status(
    document_name: str,
    ctx: TrustedContext = Depends(require_admin),
):
    return get_status(ctx.platform_id, document_name)

def _ingest_file(filepath: str, ctx: TrustedContext, module=None, access_level=None, roles=None, version="1.0") -> int:
    """Runs the full ingestion pipeline on a file already sitting on disk. Returns chunk count."""
    document_name = Path(filepath).name
    set_status(ctx.platform_id, document_name, "processing", version=version)

    try:
        raw_text = load_document_text(filepath)
        cleaned_text = clean_text(raw_text)

        registry = load_registry(REGISTRY_PATH)
        text_hash = hash_text(normalize_for_hashing(cleaned_text))
        if is_duplicate(text_hash, registry):
            raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail="Duplicate content already ingested")
        registry[text_hash] = {"document_name": document_name}
        save_registry(registry, REGISTRY_PATH)

        structured_chunks = chunk_text_structural_aware(cleaned_text)
        chunk_strings = [c for _, c in structured_chunks]
        sections = [s for s, _ in structured_chunks]

        tagged_chunks = build_chunks_with_metadata(
            chunk_strings=chunk_strings,
            filepath=filepath,
            sections=sections,
            tenant_id=ctx.tenant_id,
            module=module,
            access_level=access_level,
            roles=roles.split(",") if roles else [],
            version=version,
        )
        add_chunks_to_store(tagged_chunks)
        
        
        chunk_records = [
            {
            "chunk_index": i,
            "section": sections[i],
            "vector_id": f"{ctx.platform_id}:{document_name}:{i}",
            }
            for i in range(len(sections))
        ]
        try:
            db = SessionLocal()
            platform_row = get_or_create_platform(db, ctx.platform_id)
            tenant_row = get_or_create_tenant(db, platform_row, ctx.tenant_id)
            document_row = create_document(
                db, platform_row, tenant_row, document_name,
                module=module, language="en", access_level=access_level,
                )
            version_row = create_document_version(db, document_row, version, source_path=filepath)
            create_document_chunks(db, version_row, chunk_records)
            db.close()
        except Exception as exc:
            print(f"[warning] failed to persist document to database: {exc}")
            
        summary = summarize_document(cleaned_text)
        set_status(ctx.platform_id, document_name, "indexed", version=version, chunk_count=len(tagged_chunks))

        registry_status = load_status_registry()
        registry_status[f"{ctx.platform_id}:{document_name}"]["summary"] = summary
        save_status_registry(registry_status)   
        return len(tagged_chunks)

    except Exception as exc:
        set_status(ctx.platform_id, document_name, "failed", error=str(exc))
        raise

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
    file_existed_before = save_path.exists()  # remember this BEFORE writing anything

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    is_valid, reason = validate_document(str(save_path))
    if not is_valid:
        if not file_existed_before:
            save_path.unlink()  # only delete if WE created it
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=reason)

    try:
        chunk_count = _ingest_file(str(save_path), ctx, module, access_level, roles, version)
    except HTTPException:
        if not file_existed_before:
            save_path.unlink()  # same guard here
        raise

    return {"document_name": file.filename, "platform_id": ctx.platform_id, "chunks_stored": chunk_count, "collection_count": collection.count()}

def _remove_from_registry(document_name: str, registry: dict) -> dict:
    """
    Returns a new registry dict with any entries matching document_name removed.
    """
    return {
        h: info
        for h, info in registry.items()
        if info.get("document_name") != document_name
    }


def _delete_document_chunks(document_name: str, ctx: TrustedContext) -> None:
    where_filter = {
        "$and": [
            {"platform_id": ctx.platform_id},
            {"tenant_id": ctx.tenant_id},
            {"document_name": document_name},
        ]
    }
    collection.delete(where=where_filter)

    registry = load_registry(REGISTRY_PATH)
    registry = _remove_from_registry(document_name, registry)
    save_registry(registry, REGISTRY_PATH)


@router.delete("/documents/{document_name}")
def delete_document(document_name: str, ctx: TrustedContext = Depends(require_admin)):
    _delete_document_chunks(document_name, ctx)
    return {"deleted": document_name, "platform_id": ctx.platform_id}

@router.post("/documents/{document_name}/reindex")
def reindex_document(
    document_name: str,
    ctx: TrustedContext = Depends(require_admin),
):
    filepath = Path("sample_data") / ctx.platform_id / document_name

    if not filepath.is_file():
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f"{document_name} not found on disk")

    _delete_document_chunks(document_name, ctx)
    chunk_count = _ingest_file(str(filepath), ctx)

    return {"reindexed": document_name, "platform_id": ctx.platform_id, "chunks_stored": chunk_count}



@router.get("/documents/unanswered-questions")
def view_unanswered_questions(
    ctx: TrustedContext = Depends(require_admin),
):
    questions = get_unanswered_questions(platform_id=ctx.platform_id)
    return {
        "platform_id": ctx.platform_id,
        "count": len(questions),
        "questions": questions,
    }
    
    


@router.get("/documents/frequently-asked")
def frequently_asked_unanswered(
    ctx: TrustedContext = Depends(require_admin),
):
    questions = get_unanswered_questions(platform_id=ctx.platform_id)
    question_texts = [q["question"] for q in questions]
    counts = Counter(question_texts)
    top = counts.most_common(10)
    return {
        "platform_id": ctx.platform_id,
        "top_unanswered_questions": [{"question": q, "times_asked": n} for q, n in top]
    }