"""
Small-talk detection — Section 19.2's evidence-sufficiency check is meant
for *questions about the documentation*, not greetings/thanks/goodbyes.
Routing those through retrieve() -> fallback gives a confusing "I don't
have enough information" reply to something that isn't really a question
at all. This module catches that narrow category before retrieval runs.
"""

import re

_GREETING_PATTERNS = [
    r"^(hi|hello|hey|hiya|yo)[\s!.,]*$",
    r"^(good\s?(morning|afternoon|evening))[\s!.,]*$",
    r"^(مرحبا|هلا|السلام عليكم|صباح الخير|مساء الخير)[\s!.,]*$",
]

_THANKS_PATTERNS = [
    r"^(thanks?|thank you|thx|ty)[\s!.,]*$",
    r"^(شكرا|شكراً|يعطيك العافية|تسلم)[\s!.,]*$",
]

_GOODBYE_PATTERNS = [
    r"^(bye|goodbye|see you|later)[\s!.,]*$",
    r"^(مع السلامة|وداعا|وداعاً)[\s!.,]*$",
]


def detect_small_talk(question: str) -> str | None:
    """
    Returns "greeting" / "thanks" / "goodbye" if the message matches one
    of those categories with nothing else attached, otherwise None.
    Deliberately strict (whole-message match, not substring) -- "hi, how
    do I assign a control owner?" should still go through retrieval, only
    a bare "hi" should short-circuit.
    """
    normalized = question.strip().lower()

    for pattern in _GREETING_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return "greeting"
    for pattern in _THANKS_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return "thanks"
    for pattern in _GOODBYE_PATTERNS:
        if re.match(pattern, normalized, re.IGNORECASE):
            return "goodbye"
    return None


def small_talk_reply(kind: str, language: str = "en") -> str:
    replies = {
        "greeting": {
            "en": "Hello! Ask me anything about your platform's documentation.",
            "ar": "مرحباً! اسألني أي شي عن وثائق منصتك.",
        },
        "thanks": {
            "en": "You're welcome! Let me know if you have another question.",
            "ar": "العفو! اعلمني لو عندك سؤال ثاني.",
        },
        "goodbye": {
            "en": "Goodbye! Come back anytime you have a question.",
            "ar": "مع السلامة! ارجع أي وقت تحتاج تسأل شي.",
        },
    }
    return replies[kind].get(language, replies[kind]["en"])