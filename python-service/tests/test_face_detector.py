import numpy as np
import pytest

from recog_core.vision.face_detector import DEFAULT_MODEL_PATH, BoundingBox, FaceDetector


@pytest.fixture(scope="module")
def detector():
    if not DEFAULT_MODEL_PATH.exists():
        pytest.skip(
            f"Face detection model not found at {DEFAULT_MODEL_PATH} -- "
            "run scripts/download_face_model.sh first."
        )
    d = FaceDetector()
    yield d
    d.close()


def test_detect_returns_empty_list_on_blank_frame(detector):
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    assert detector.detect(blank) == []


def test_detect_returns_bounding_box_list_on_noise_frame(detector):
    # Not a real face, so we don't assert on detection count -- this is a no-crash /
    # type-correctness regression guard, not an accuracy benchmark (real accuracy is checked
    # manually against the live webcam per the phase-1 plan; a real face photo would need to
    # be committed to the repo, which conflicts with this project's no-personal-data policy).
    noise = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    boxes = detector.detect(noise)
    assert isinstance(boxes, list)
    assert all(isinstance(b, BoundingBox) for b in boxes)
