import re
import unicodedata

MAX_QUERY_LENGTH = 2000


def preprocess_query(raw_query: str) -> str:
    if not raw_query or not raw_query.strip():
        raise ValueError("Query cannot be empty.")

    text = unicodedata.normalize("NFKC", raw_query)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > MAX_QUERY_LENGTH:
        text = text[:MAX_QUERY_LENGTH]

    return text