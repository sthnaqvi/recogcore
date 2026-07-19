from __future__ import annotations

from recog_core.conversation.intents import match_intent

NO_MATCH_RESPONSE = "Sorry, I didn't quite catch that."


def get_response(text: str, mode: str = "rules") -> str:
    """Tries rule-based intents first (fast, free, deterministic). If `mode == 'llm'` and no rule
    matched, falls through to the LLM responder for open-ended replies -- this hybrid default
    keeps cost near zero for common interactions while still allowing open-ended chat."""
    canned = match_intent(text)
    if canned is not None:
        return canned

    if mode == "llm":
        from recog_core.conversation.llm_responder import get_llm_response

        return get_llm_response(text)

    return NO_MATCH_RESPONSE
