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


def test_identify_returns_unknown_when_two_people_are_ambiguously_close(tmp_path):
    # Query sits at distance 0.40 from alice and 0.43 from bob -- both within threshold, but
    # the gap (0.03) is under the 0.05 ambiguity margin, so guessing between them is unsafe.
    alice_ref = np.zeros(DIM)
    bob_ref = np.zeros(DIM)
    bob_ref[0] = 0.83

    path = _make_embeddings_file(tmp_path, {"alice": [alice_ref], "bob": [bob_ref]})
    recognizer = Recognizer(path, threshold=0.6, margin=0.05)

    query = np.zeros(DIM)
    query[0] = 0.4
    result = recognizer.identify(query)

    assert result.is_known is False
    assert result.name == "unknown"


def test_identify_aggregates_over_top_k_not_single_min(tmp_path):
    # One outlier training photo sits right on the query; the person's other photos are far
    # away. The old min-based logic would match on the outlier alone; top-k mean must not.
    outlier = np.zeros(DIM)
    far1 = np.zeros(DIM)
    far1[0] = 0.95
    far2 = np.zeros(DIM)
    far2[1] = 0.95

    path = _make_embeddings_file(tmp_path, {"alice": [outlier, far1, far2]})
    recognizer = Recognizer(path, threshold=0.6, margin=0.05)

    query = np.zeros(DIM)  # distance 0 to the outlier, 0.95 to the other two -> top-3 mean ~0.63
    result = recognizer.identify(query)

    assert result.is_known is False


def test_identify_all_never_assigns_same_person_to_two_faces(tmp_path):
    alice_ref = np.zeros(DIM)
    path = _make_embeddings_file(tmp_path, {"alice": [alice_ref]})
    recognizer = Recognizer(path, threshold=0.6, margin=0.05)

    strong_match = np.zeros(DIM)
    strong_match[0] = 0.1  # distance 0.1
    weaker_match = np.zeros(DIM)
    weaker_match[0] = 0.4  # distance 0.4 -- also within threshold on its own

    results = recognizer.identify_all([weaker_match, strong_match])

    assert results[1].name == "alice"
    assert results[1].is_known is True
    assert results[0].name == "unknown"
    assert results[0].is_known is False


def test_identify_all_keeps_distinct_people_distinct(tmp_path):
    alice_ref = np.zeros(DIM)
    bob_ref = np.zeros(DIM)
    bob_ref[0] = 2.0

    path = _make_embeddings_file(tmp_path, {"alice": [alice_ref], "bob": [bob_ref]})
    recognizer = Recognizer(path, threshold=0.6, margin=0.05)

    near_alice = np.zeros(DIM)
    near_alice[0] = 0.1
    near_bob = np.zeros(DIM)
    near_bob[0] = 1.9

    results = recognizer.identify_all([near_alice, near_bob])

    assert results[0].name == "alice"
    assert results[1].name == "bob"
