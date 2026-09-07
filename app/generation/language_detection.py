"""
Auto-detect the answer language from the question text itself, so the
frontend doesn't need to hardcode language="en" and the user doesn't need
a language toggle -- ask in Arabic, get Arabic back; ask in English, get
English back.

Deliberately simple (character-range check, not a full language-detection
library): Arabic questions are the one case we need to distinguish from
everything else, and Unicode range 0600-06FF covers Arabic script
reliably without adding a dependency.
"""

import re

_ARABIC_RANGE = re.compile(r"[\u0600-\u06FF]")


def detect_language(text: str) -> str:
    """
    Returns "ar" if the text contains any Arabic-script characters,
    otherwise "en". A question mixing scripts (e.g. an English question
    quoting one Arabic term) is treated as Arabic -- erring toward
    Arabic on any Arabic content matches user expectation better than
    the reverse.
    """
    return "ar" if _ARABIC_RANGE.search(text) else "en"
