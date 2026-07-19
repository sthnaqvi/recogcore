from __future__ import annotations

import pickle
from pathlib import Path

import face_recognition
import numpy as np


def generate_embedding(
    face_image: np.ndarray, face_location: tuple[int, int, int, int] | None = None
) -> np.ndarray | None:
    """`face_image` is a BGR image (OpenCV convention) containing a single face. Returns None
    if no face is found in it.

    `face_location` is an optional (top, right, bottom, left) box of the face *within*
    `face_image`. When the caller already located the face (the live loop, via MediaPipe),
    passing that tight box skips dlib's own redundant face-detection pass (~3-4x faster per
    call) while still letting dlib run its landmark alignment on a tight box -- the same
    alignment the training photos get (where dlib detects the face itself), so live and
    training embeddings stay directly comparable. An earlier version passed the whole padded
    crop as the location, which subtly misaligned live embeddings relative to training ones.
    When `face_location` is None, dlib detects the face itself (slower, used off the hot path)."""
    rgb = np.ascontiguousarray(face_image[:, :, ::-1])
    locations = [face_location] if face_location is not None else None
    encodings = face_recognition.face_encodings(rgb, known_face_locations=locations)
    return encodings[0] if encodings else None


def build_known_faces_db(training_dir: Path) -> dict[str, list[np.ndarray]]:
    """Walks `training_dir/faces/<person_name>/*.jpg` and returns {person_name: [encodings]}."""
    faces_dir = training_dir / "faces"
    known: dict[str, list[np.ndarray]] = {}
    if not faces_dir.exists():
        return known

    for person_dir in sorted(faces_dir.iterdir()):
        if not person_dir.is_dir():
            continue
        encodings = []
        for photo_path in sorted(person_dir.glob("*.jpg")):
            image = face_recognition.load_image_file(str(photo_path))
            found = face_recognition.face_encodings(image)
            if found:
                encodings.append(found[0])
        if encodings:
            known[person_dir.name] = encodings
    return known


def save_known_faces_db(known: dict[str, list[np.ndarray]], embeddings_path: Path) -> None:
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(embeddings_path, "wb") as f:
        pickle.dump(known, f)


def load_known_faces_db(embeddings_path: Path) -> dict[str, list[np.ndarray]]:
    if not embeddings_path.exists():
        return {}
    with open(embeddings_path, "rb") as f:
        return pickle.load(f)
