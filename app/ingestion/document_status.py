import json
from pathlib import Path
from datetime import datetime, timezone

STATUS_PATH = "document_status.json"


def load_status_registry(path: str = STATUS_PATH) -> dict:
    if not Path(path).exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_status_registry(registry: dict, path: str = STATUS_PATH) -> None:
    with open(path, "w") as f:
        json.dump(registry, f, indent=2)


def _key(platform_id: str, document_name: str) -> str:
    return f"{platform_id}:{document_name}"


def set_status(
    platform_id: str,
    document_name: str,
    status: str,
    version: str = None,
    chunk_count: int = None,
    error: str = None,
    path: str = STATUS_PATH,
) -> None:
    registry = load_status_registry(path)
    key = _key(platform_id, document_name)
    entry = registry.get(key, {"history": []})

    was_indexed = entry.get("status") == "indexed"

    entry["last_attempt_status"] = status
    entry["last_attempt_time"] = datetime.now(timezone.utc).isoformat()
    if error:
        entry["last_error"] = error
    else:
        entry.pop("last_error", None)

    # Don't let a failed re-upload attempt overwrite a genuinely indexed document
    if status == "failed" and was_indexed:
        pass  # keep status as "indexed", just record the failed attempt above
    else:
        entry["status"] = status
        if version:
            entry["version"] = version
        if chunk_count is not None:
            entry["chunk_count"] = chunk_count

    if status == "indexed" and version:
        entry["history"].append({
            "version": version,
            "timestamp": entry["last_attempt_time"],
            "chunk_count": chunk_count,
        })

    registry[key] = entry
    save_status_registry(registry, path)


def get_status(platform_id: str, document_name: str, path: str = STATUS_PATH) -> dict:
    registry = load_status_registry(path)
    return registry.get(_key(platform_id, document_name), {"status": "not_found"})