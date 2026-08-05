from app.generation.llm_client import call_llm


def summarize_document(text: str, max_chars: int = 2000) -> str:
    """
    Generates a short summary of a document's content using the LLM.
    Truncates very long documents before summarizing, since a summary
    doesn't need the full text to capture the gist.
    """
    excerpt = text[:max_chars]

    messages = [
        {"role": "system", "content": "Summarize the following document in 2-3 concise sentences. Do not invent details not present in the text."},
        {"role": "user", "content": excerpt},
    ]

    return call_llm(messages)