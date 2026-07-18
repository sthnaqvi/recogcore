from __future__ import annotations

import pickle
from pathlib import Path

import face_recognition
import numpy as np


def generate_embedding(face_image: np.ndarray) -> np.ndarray | None:
    """`face_image` is a BGR image (OpenCV convention) containing a single face -- either a
    tight crop from the live detector or a full training photo. Returns None if no face is
    found in it."""
    rgb = np.ascontiguousarray(face_image[:, :, ::-1])
    encodings = face_recognition.face_encodings(rgb)
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
