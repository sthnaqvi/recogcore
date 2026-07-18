from __future__ import annotations

import random
import time
from typing import Callable

from recog_core.vision.recognizer import RecognitionResult


def build_greeting(
    result: RecognitionResult, known_phrasings: list[str], unknown_phrasings: list[str]
) -> str:
    """Known person -> a random pick from `known_phrasings` (formatted with {name}); unknown ->
    a random pick from `unknown_phrasings`. Phrasing lists are config-driven (config.yaml:
    greetings.known / greetings.unknown) so wording changes don't need a code change."""
    if result.is_known:
        template = random.choice(known_phrasings)
        return template.format(name=result.name)
    return random.choice(unknown_phrasings)


class GreetingCooldown:
    """Tracks per-person 'last greeted at' so the same person isn't re-greeted every frame while
    they linger in view. Keyed by `RecognitionResult.name` -- known people by their own name,
    unknown faces all share the "unknown" key, so strangers aren't re-greeted every frame either.
    `clock` is injectable so tests don't depend on real wall-clock time."""

    def __init__(self, cooldown_seconds: float, clock: Callable[[], float] = time.time) -> None:
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._last_greeted_at: dict[str, float] = {}

    def should_greet(self, person_key: str) -> bool:
        last = self._last_greeted_at.get(person_key)
        if last is None:
            return True
        return (self._clock() - last) >= self._cooldown_seconds

    def mark_greeted(self, person_key: str) -> None:
        self._last_greeted_at[person_key] = self._clock()
