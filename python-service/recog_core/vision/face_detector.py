from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "blaze_face_short_range.tflite"


@dataclass
class BoundingBox:
    x: int
    y: int
    w: int
    h: int
    confidence: float


class FaceDetector:
    """Wraps MediaPipe's face detector behind a single `detect(frame) -> list[BoundingBox]`
    method, so Phase 2 can swap the underlying model without touching callers."""

    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH, min_detection_confidence: float = 0.5) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Face detection model not found at {model_path}. "
                "Run scripts/download_face_model.sh first."
            )
        base_options = mp_python.BaseOptions(model_asset_path=str(model_path))
        options = mp_vision.FaceDetectorOptions(
            base_options=base_options, min_detection_confidence=min_detection_confidence
        )
        self._detector = mp_vision.FaceDetector.create_from_options(options)

    def detect(self, frame: np.ndarray) -> list[BoundingBox]:
        """`frame` is a BGR image (OpenCV convention)."""
        rgb = frame[:, :, ::-1]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        result = self._detector.detect(mp_image)

        boxes = []
        for detection in result.detections:
            bbox = detection.bounding_box
            confidence = detection.categories[0].score if detection.categories else 0.0
            boxes.append(
                BoundingBox(x=bbox.origin_x, y=bbox.origin_y, w=bbox.width, h=bbox.height, confidence=confidence)
            )
        return boxes

    def close(self) -> None:
        self._detector.close()
