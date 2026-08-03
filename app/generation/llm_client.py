import os
from typing import List, Dict

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "1024"))

def call_llm(messages: List[Dict[str, str]]) -> str:
    """
    messages: the list produced by app.generation.prompts.build_messages()
      — [{"role": "system", "content": ...}, {"role": "user", "content": ...}, ...]

    Returns: the assistant's answer text.
    """
    if LLM_PROVIDER == "groq":
        return _call_groq(messages)
    raise NotImplementedError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER!r}")

def _call_groq(messages: List[Dict[str, str]]) -> str:
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file (never commit .env)."
        )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        messages=messages,
    )
    return response.choices[0].message.content