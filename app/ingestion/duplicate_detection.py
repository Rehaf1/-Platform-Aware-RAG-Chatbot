import hashlib
import json
import re
from pathlib import Path

HEADING_PATTERNS = [
    r'^#{1,6}\s+(.+)',              # Markdown: captures text after the #'s
    r'^Section:\s*(.+)',            # captures text after "Section:"
    r'^Chapter\s+\d+[:.]?\s*(.+)',  # captures text after "Chapter N:"
    r'^\d+(?:\.\d+)*\s+(.+)',       # captures text after the number
]


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_registry(registry_path: str) -> dict:
    path = Path(registry_path)
    if not path.exists():
        return {}
    with open(registry_path, "r") as file:
        return json.load(file)

def save_registry(registry: dict, registry_path: str) -> None:
    with open(registry_path, "w") as file:
        json.dump(registry, file)

def is_duplicate(text_hash: str, registry: dict) -> bool:
    return text_hash in registry

def normalize_for_hashing(text: str) -> str:
    """
    Normalizes text before hashing so formatting differences (line breaks,
    heading syntax) don't prevent near-duplicate detection. More aggressive
    normalization = more duplicates caught, but higher risk of false positives.
    """
    for pattern in HEADING_PATTERNS:
        text = re.sub(pattern, r'\1', text, flags=re.MULTILINE)
        
    text = re.sub(r'\s+', ' ', text)

    return text.strip().lower()