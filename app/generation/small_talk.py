"""
Small-talk detection — Section 19.2's evidence-sufficiency check is meant
for *questions about the documentation*, not conversational filler.
Routing those through retrieve() -> fallback gives a confusing "I don't
have enough information" reply to something that isn't really a question
about the platform at all. This module catches that category before
retrieval runs.

Categories covered: greeting, thanks, goodbye, how_are_you, who_are_you,
help, capability. Each is matched as a *whole message* (not a substring)
so "hi, how do I assign a control owner?" still goes through retrieval —
only a bare small-talk message short-circuits.
"""

import re

_PATTERNS: dict[str, list[str]] = {
    "greeting": [
        r"^(hi|hello|hey|hiya|yo)[\s!.,]*$",
        r"^(good\s?(morning|afternoon|evening))[\s!.,]*$",
        r"^(مرحبا|هلا|السلام عليكم|صباح الخير|مساء الخير|اهلا|أهلاً)[\s!.,]*$",
    ],
    "thanks": [
        r"^(thanks?|thank you|thx|ty|appreciate it)[\s!.,]*$",
        r"^(شكرا|شكراً|يعطيك العافية|تسلم|تسلمين|مشكور)[\s!.,]*$",
    ],
    "goodbye": [
        r"^(bye|goodbye|see you|later|take care)[\s!.,]*$",
        r"^(مع السلامة|وداعا|وداعاً|باي)[\s!.,]*$",
    ],
    "how_are_you": [
        r"^how are you[\s?!.,]*$",
        r"^how('s| is) it going[\s?!.,]*$",
        r"^(كيف حالك|كيفك|شلونك|شخبارك|إيش أخبارك)[\s؟?!.,]*$",
    ],
    "who_are_you": [
        r"^who are you[\s?!.,]*$",
        r"^what('s| is) your name[\s?!.,]*$",
        r"^(مين انت|من انت|ايش اسمك|وش اسمك)[\s؟?!.,]*$",
    ],
    "help": [
        r"^help[\s!.,]*$",
        r"^i need help[\s!.,]*$",
        r"^(ساعدني|احتاج مساعدة|أحتاج مساعدة|مساعدة)[\s!.,]*$",
    ],
    "capability": [
        r"^what can you do[\s?!.,]*$",
        r"^what do you do[\s?!.,]*$",
        r"^(وش تقدر تسوي|ايش تقدر تسوي|وش تسوي|إيش تسوي)[\s؟?!.,]*$",
    ],
}

_REPLIES: dict[str, dict[str, str]] = {
    "greeting": {
        "en": "Hello! Ask me anything about your platform's documentation.",
        "ar": "مرحباً! اسألني أي شي عن وثائق منصتك.",
    },
    "thanks": {
        "en": "You're welcome! Let me know if you have another question.",
        "ar": "العفو! خبرني لو عندك سؤال ثاني.",
    },
    "goodbye": {
        "en": "Goodbye! Come back anytime you have a question.",
        "ar": "مع السلامة! ارجع أي وقت تحتاج تسأل شي.",
    },
    "how_are_you": {
        "en": "I'm doing well, thanks for asking! How can I help with your platform's documentation?",
        "ar": "أنا بخير، شكراً لسؤالك! كيف أقدر أساعدك بخصوص وثائق منصتك؟",
    },
    "who_are_you": {
        "en": "I'm the APTWatch assistant -- I answer questions using your platform's approved documentation.",
        "ar": "أنا مساعد APTWatch -- أجاوب على أسئلتك بالاعتماد على وثائق منصتك المعتمدة.",
    },
    "help": {
        "en": "I can answer questions about your platform's documentation -- just ask, for example \"How do I assign a control owner?\"",
        "ar": "أقدر أجاوب على أسئلتك عن وثائق منصتك -- بس اسأل، مثلاً \"كيف أعيّن مسؤول رقابة؟\"",
    },
    "capability": {
        "en": "I answer questions grounded in your platform's approved documentation, with sources cited for every answer.",
        "ar": "أجاوب على أسئلتك بالاعتماد على وثائق منصتك المعتمدة، مع ذكر مصادر كل جواب.",
    },
}


def detect_small_talk(question: str) -> str | None:
    normalized = question.strip().lower()
    for kind, patterns in _PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, normalized, re.IGNORECASE):
                return kind
    return None


def small_talk_reply(kind: str, language: str = "en") -> str:
    return _REPLIES[kind].get(language, _REPLIES[kind]["en"])
