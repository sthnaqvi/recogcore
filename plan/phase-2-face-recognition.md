# Phase 2 — Face recognition + training

**Est. 15–20 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Go from "a face is present" (Phase 1) to "this is Mom / this is unknown." Build the training
capture flow, embedding generation, and known/unknown classification with a tunable threshold —
all reading/writing under the gitignored `data/` directory so no personal photos or embeddings
ever land in the repo.

## Task breakdown

1. Add `face_recognition` (dlib-based) to `python-service` deps; confirm it builds against the
   Phase 0 Python 3.11 venv on this Mac (dlib compilation is the most likely install snag —
   `brew install cmake` first if the wheel build fails).
2. Define the on-disk training data layout under `data/` (gitignored, per `PLAN.md`'s
   open-source design constraint): `data/training/faces/<person_name>/*.jpg` for raw captured photos,
   `data/training/embeddings/<person_name>.npy` (or one combined `data/training/embeddings/known_faces.pkl`) for
   generated embeddings. `data/README.md` (from Phase 0) gets updated to describe this concretely.
3. Write `recog_core/vision/capture_training_photos.py` — a CLI-driven capture flow (`recogcore
   train --capture <name>`): opens the camera via `HardwareProvider`, guides the user to capture
   15–20 shots with prompts to vary angle/lighting, saves to `data/training/faces/<name>/`.
4. Write `recog_core/vision/embeddings.py`: `generate_embedding(image) -> np.ndarray` (wraps
   `face_recognition.face_encodings`), plus `build_known_faces_db(data_dir) -> dict[str,
   list[np.ndarray]]` that walks `data/training/faces/*/` and produces/saves the embeddings file.
5. Wire `recogcore train --build` (or fold into the same command) to run
   `build_known_faces_db` and write `data/training/embeddings/known_faces.pkl` — this is the actual
   `recogcore-train` console entry point stubbed in Phase 0.
6. Write `recog_core/vision/recognizer.py`: `Recognizer` class that loads the embeddings file
   once, exposes `identify(face_embedding) -> RecognitionResult` (`name`, `is_known: bool`,
   `confidence: float`), comparing via `face_recognition.face_distance` (or cosine distance if
   switching libraries later).
7. Make the known/unknown threshold a **config value**, not hardcoded (`config.yaml:
   recognition.threshold`, default ~0.6 euclidean distance per the original plan) — this is the
   knob that gets tuned per-install since it's sensitive to camera/lighting, and must not require
   a code change to adjust.
8. Extend the Phase 1 capture loop (`recog_core/vision/loop.py`) to run detection → crop face →
   `generate_embedding` → `recognizer.identify()` → draw name (or "Unknown") + confidence on the
   preview box instead of just a generic bounding box.
9. Handle the empty-database case cleanly: a fresh clone with no trained faces yet should not
   crash — `Recognizer` treats every face as unknown until `data/training/embeddings/` has entries, and
   the loop should print a clear "no trained faces yet — run `recogcore train`" hint.
10. Threshold tuning pass: capture test sessions in varied lighting for at least 2 trained
    people + yourself as a control "unknown," compare distances, adjust the default threshold in
    `config.example.yaml` based on what actually separates known from unknown on this hardware.
11. Tests in `tests/test_recognizer.py`: given a small fixture embeddings dict and hand-crafted
    distance values, assert `identify()` classifies known/unknown correctly at the boundary —
    this tests the classification logic, not the ML model itself.

## File/folder layout created by this phase

```
robot-assistant/
├── data/
│   └── training/                  # gitignored
│       ├── faces/
│       │   └── <person_name>/*.jpg
│       └── embeddings/
│           └── known_faces.pkl
└── python-service/
    ├── tests/
    │   └── test_recognizer.py
    └── recog_core/
        └── vision/
            ├── capture_training_photos.py
            ├── embeddings.py
            └── recognizer.py
```
