# Known Issues — Write Path

## ~~1. `last_error` field is stale after a successful attempt~~ ✅ FIXED 2026-08-10
Fixed in `document_status.py`'s `set_status` — now clears `last_error` when a later attempt succeeds.

## ~~2. Documents table accumulates duplicate rows on reindex/re-upload~~ ✅ FIXED 2026-08-10
Fixed by adding `get_or_create_document` to `crud.py`, and adding a `document_row.status = "indexed"` update after successful ingestion in `_ingest_file`.

## 3. Cross-format duplicate check blocks legitimate reindex
**File:** `app/ingestion/duplicate_detection.py` + `_ingest_file`
**Symptom:** Reindexing a document can fail with `409 Duplicate` if the same content is already indexed under a *different* filename/format.
**Status:** Open.

## 4. Upload doesn't back up original file content on overwrite failure
**File:** `app/api/documents.py` (`upload_document`)
**Status:** Open, low priority — accepted as a known limitation.