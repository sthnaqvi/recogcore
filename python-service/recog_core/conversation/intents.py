from __future__ import annotations

import random
import re
from dataclasses import dataclass


@dataclass
class Intent:
    name: str
    pattern: "re.Pattern[str]"
    responses: list[str]


INTENTS: list[Intent] = [
    Intent(
        "how_are_you",
        re.compile(r"\bhow are you\b", re.I),
        ["I'm doing great, thanks for asking!", "Doing well! How about you?"],
    ),
    Intent(
        "weather",
        re.compile(r"\bweather\b", re.I),
        ["I can't check the weather yet, sorry -- maybe in a future update!"],
    ),
    Intent(
        "goodbye",
        re.compile(r"\b(goodbye|bye|see you|later)\b", re.I),
        ["Goodbye! See you soon.", "Bye for now!"],
    ),
    Intent(
        "thanks",
        re.compile(r"\b(thank you|thanks)\b", re.I),
        ["You're welcome!", "Anytime!"],
    ),
    Intent(
        "who_are_you",
        re.compile(r"\b(what'?s your name|who are you)\b", re.I),
        ["I'm RecogCore, your home entryway assistant."],
    ),
]


def match_intent(text: str) -> str | None:
    """Returns a canned response if `text` matches a known rule, else None (the caller falls
    through to the LLM path if `conversation.mode: llm` is set)."""
    for intent in INTENTS:
        if intent.pattern.search(text):
            return random.choice(intent.responses)
    return None
