from __future__ import annotations

import os

SYSTEM_PROMPT = (
    "You are RecogCore, a friendly home-entryway assistant speaking out loud to someone who just "
    "walked in. Keep replies to 1-2 short sentences -- this is spoken conversation, not text chat."
)
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
FALLBACK_RESPONSE = "I don't have anything smart to say about that yet."


def get_llm_response(text: str, model: str = DEFAULT_MODEL) -> str:
    """Calls the Anthropic API for an open-ended reply the rule-based path can't cover. Requires
    ANTHROPIC_API_KEY in .env (never committed, never logged); falls back to a canned response
    if the key is missing so a misconfigured install doesn't crash the conversation loop."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return FALLBACK_RESPONSE

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=100,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    return message.content[0].text.strip()
