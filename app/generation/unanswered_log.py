import json
from pathlib import Path
from datetime import datetime, timezone

LOG_PATH = "unanswered_questions.json"


def log_unanswered_question(
    question: str,
    platform_id: str,
    tenant_id: str,
    reason: str = "insufficient_evidence",
    path: str = LOG_PATH,
) -> None:
    entries = []
    if Path(path).exists():
        with open(path, "r") as f:
            entries = json.load(f)

    entries.append({
        "question": question,
        "platform_id": platform_id,
        "tenant_id": tenant_id,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def get_unanswered_questions(platform_id: str = None, path: str = LOG_PATH) -> list:
    if not Path(path).exists():
        return []
    with open(path, "r") as f:
        entries = json.load(f)
    if platform_id:
        entries = [e for e in entries if e["platform_id"] == platform_id]
    return entries