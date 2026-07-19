from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import face_recognition
import numpy as np

from recog_core.vision.embeddings import load_known_faces_db

DEFAULT_THRESHOLD = 0.5
DEFAULT_AMBIGUITY_MARGIN = 0.05
TOP_K = 3  # aggregate over the k best-matching training photos, not the single minimum


@dataclass
class RecognitionResult:
    name: str
    is_known: bool
    confidence: float


class Recognizer:
    """Loads known-face embeddings once and classifies new embeddings against them.

    Distance is Euclidean (face_recognition.face_distance). A face is "known" only when BOTH:
    - its aggregated distance to the closest trained person is at or below `threshold`, AND
    - the second-closest trained person is at least `margin` further away (otherwise the match
      is ambiguous -- e.g. two similar-looking family members -- and guessing between them is
      worse than saying "unknown").

    Per-person distance is the mean of the TOP_K smallest distances against that person's
    training photos, not the single minimum -- one outlier training photo (bad lighting, odd
    angle) can be spuriously close to anyone, and taking the raw min let exactly that outlier
    decide the match.

    `threshold` and `margin` are config values (config.yaml: recognition.threshold /
    recognition.ambiguity_margin), not hardcoded, since they're sensitive to camera/lighting and
    who's trained (families with young children need stricter settings -- the underlying encoder
    is trained mostly on adult faces, so kids' embeddings cluster much closer together).
    """

    def __init__(
        self,
        embeddings_path: Path,
        threshold: float = DEFAULT_THRESHOLD,
        margin: float = DEFAULT_AMBIGUITY_MARGIN,
    ) -> None:
        self._threshold = threshold
        self._margin = margin
        self._known: dict[str, list[np.ndarray]] = load_known_faces_db(embeddings_path)

    def has_known_faces(self) -> bool:
        return bool(self._known)

    def _person_distances(self, embedding: np.ndarray) -> dict[str, float]:
        scores: dict[str, float] = {}
        for name, encodings in self._known.items():
            distances = np.sort(face_recognition.face_distance(encodings, embedding))
            k = min(TOP_K, len(distances))
            scores[name] = float(np.mean(distances[:k]))
        return scores

    def identify(self, embedding: np.ndarray) -> RecognitionResult:
        if not self._known:
            return RecognitionResult(name="unknown", is_known=False, confidence=0.0)

        scores = self._person_distances(embedding)
        best_name = min(scores, key=scores.get)
        best_distance = scores[best_name]
        second_best = min(
            (d for name, d in scores.items() if name != best_name), default=float("inf")
        )

        is_known = best_distance <= self._threshold and (second_best - best_distance) >= self._margin
        confidence = max(0.0, 1.0 - best_distance)
        return RecognitionResult(
            name=best_name if is_known else "unknown",
            is_known=is_known,
            confidence=confidence,
        )

    def identify_all(self, embeddings: list[np.ndarray]) -> list[RecognitionResult]:
        """Identify several faces from the same frame, enforcing that one trained person can
        only be assigned to ONE face per frame -- two people cannot both be "Jazib" at once.
        When multiple faces match the same name, the strongest match keeps it and the rest are
        demoted to unknown."""
        results = [self.identify(embedding) for embedding in embeddings]

        best_index_by_name: dict[str, int] = {}
        for i, result in enumerate(results):
            if not result.is_known:
                continue
            current = best_index_by_name.get(result.name)
            if current is None or result.confidence > results[current].confidence:
                best_index_by_name[result.name] = i

        for i, result in enumerate(results):
            if result.is_known and best_index_by_name[result.name] != i:
                results[i] = replace(result, name="unknown", is_known=False)
        return results
