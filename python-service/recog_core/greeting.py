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


class GreetingStabilizer:
    """Requires the same identity to be seen in `required_consecutive` recognition passes IN A
    ROW before it becomes eligible for greeting.

    Without this, a single misclassified frame triggers a greeting immediately: recognition
    flickering between identities (varying angle/lighting frame to frame, plus similar-looking
    family members) once greeted one real person as four different identities in a row --
    each wrong name was a brand-new cooldown key, so every flicker fired a fresh greeting.
    A wrong identity that appears for only one or two passes never reaches the streak
    requirement and is silently dropped.

    "unknown" is held to double the streak requirement: it's not just genuine strangers -- it's
    also the fallback bucket for every rejected/ambiguous classification (camera warming up,
    someone mid-turn), so it flickers into view far more easily than a confident named match."""

    UNKNOWN_MULTIPLIER = 2

    def __init__(self, required_consecutive: int = 3) -> None:
        self._required = required_consecutive
        self._streaks: dict[str, int] = {}

    def observe(self, names_in_frame) -> set[str]:
        """Call once per recognition pass with every identity seen in that pass (including
        "unknown"). Returns the identities whose streak has reached the stability requirement."""
        names = set(names_in_frame)
        for tracked in list(self._streaks):
            if tracked not in names:
                del self._streaks[tracked]

        stable: set[str] = set()
        for name in names:
            self._streaks[name] = self._streaks.get(name, 0) + 1
            required = self._required * (self.UNKNOWN_MULTIPLIER if name == "unknown" else 1)
            if self._streaks[name] >= required:
                stable.add(name)
        return stable


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
