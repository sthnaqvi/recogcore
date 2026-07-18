from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import face_recognition
import numpy as np

from recog_core.vision.embeddings import load_known_faces_db

DEFAULT_THRESHOLD = 0.6


@dataclass
class RecognitionResult:
    name: str
    is_known: bool
    confidence: float


class Recognizer:
    """Loads known-face embeddings once and classifies new embeddings against them.

    Distance is Euclidean (face_recognition.face_distance); a face is "known" when its distance
    to the closest known embedding is at or below `threshold`. `threshold` is a config value
    (config.yaml: recognition.threshold), not hardcoded, since it's sensitive to camera/lighting
    and needs per-install tuning.
    """

    def __init__(self, embeddings_path: Path, threshold: float = DEFAULT_THRESHOLD) -> None:
        self._threshold = threshold
        self._known: dict[str, list[np.ndarray]] = load_known_faces_db(embeddings_path)

    def has_known_faces(self) -> bool:
        return bool(self._known)

    def identify(self, embedding: np.ndarray) -> RecognitionResult:
        if not self._known:
            return RecognitionResult(name="unknown", is_known=False, confidence=0.0)

        best_name = "unknown"
        best_distance = float("inf")
        for name, encodings in self._known.items():
            distances = face_recognition.face_distance(encodings, embedding)
            min_distance = float(np.min(distances))
            if min_distance < best_distance:
                best_distance = min_distance
                best_name = name

        is_known = best_distance <= self._threshold
        confidence = max(0.0, 1.0 - best_distance)
        return RecognitionResult(
            name=best_name if is_known else "unknown",
            is_known=is_known,
            confidence=confidence,
        )
