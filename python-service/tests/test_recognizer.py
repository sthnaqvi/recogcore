import pickle
from pathlib import Path

import numpy as np
import pytest

from recog_core.vision.recognizer import Recognizer

DIM = 128  # matches face_recognition's real embedding size


def _make_embeddings_file(tmp_path: Path, known: dict) -> Path:
    path = tmp_path / "known_faces.pkl"
    with open(path, "wb") as f:
        pickle.dump(known, f)
    return path


def test_identify_returns_unknown_when_no_embeddings_file(tmp_path):
    recognizer = Recognizer(tmp_path / "missing.pkl", threshold=0.6)
    assert not recognizer.has_known_faces()

    result = recognizer.identify(np.zeros(DIM))
    assert result.is_known is False
    assert result.name == "unknown"
    assert result.confidence == 0.0


def test_identify_matches_known_face_within_threshold(tmp_path):
    reference = np.zeros(DIM)
    path = _make_embeddings_file(tmp_path, {"alice": [reference]})
    recognizer = Recognizer(path, threshold=0.6)

    close_embedding = reference.copy()
    close_embedding[0] = 0.5  # euclidean distance = 0.5, within threshold
    result = recognizer.identify(close_embedding)

    assert result.is_known is True
    assert result.name == "alice"
    assert result.confidence == pytest.approx(0.5, abs=1e-6)


def test_identify_rejects_face_outside_threshold(tmp_path):
    reference = np.zeros(DIM)
    path = _make_embeddings_file(tmp_path, {"alice": [reference]})
    recognizer = Recognizer(path, threshold=0.6)

    far_embedding = reference.copy()
    far_embedding[0] = 0.7  # euclidean distance = 0.7, outside threshold
    result = recognizer.identify(far_embedding)

    assert result.is_known is False
    assert result.name == "unknown"


def test_identify_picks_closest_of_multiple_people(tmp_path):
    alice_ref = np.zeros(DIM)
    bob_ref = np.zeros(DIM)
    bob_ref[0] = 2.0  # far from the origin

    path = _make_embeddings_file(tmp_path, {"alice": [alice_ref], "bob": [bob_ref]})
    recognizer = Recognizer(path, threshold=0.6)

    query = np.zeros(DIM)
    query[0] = 0.1  # much closer to alice than bob
    result = recognizer.identify(query)

    assert result.name == "alice"
    assert result.is_known is True
