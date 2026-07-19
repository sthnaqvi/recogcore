# Phase 2 — Face recognition + training

**Est. 15–20 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Go from "a face is present" (Phase 1) to "this is Mom / this is unknown." Build the training
capture flow, embedding generation, and known/unknown classification with a tunable threshold —
all reading/writing under the gitignored `data/` directory so no personal photos or embeddings
ever land in the repo.

## Task breakdown

1. Add `face_recognition` (dlib-based) to `python-service` deps; confirmed it builds cleanly
   from source against the Phase 0 Python 3.10 venv on this Mac (`cmake` was already available
   via Homebrew, so no extra install snag in practice).
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
   **Fixed after a user-reported lag bug** (see `../KNOWN_ISSUES.md`): `generate_embedding()`
   was calling `face_encodings()` without `known_face_locations`, so it silently re-ran dlib's
   own HOG face detector on every already-cropped face on every live-loop frame (~30ms/call).
   Now passes the crop's own coordinates explicitly, skipping the redundant re-detection
   (~30ms → ~8ms/call) — this, plus capping camera resolution (Phase 0) and throttling how often
   the live loop re-runs recognition (Phase 1's `loop.py`), fixed a real "video is very laggy"
   report.
5. Wire `recogcore train --build` (or fold into the same command) to run
   `build_known_faces_db` and write `data/training/embeddings/known_faces.pkl` — this is the actual
   `recogcore-train` console entry point stubbed in Phase 0.
6. Write `recog_core/vision/recognizer.py`: `Recognizer` class that loads the embeddings file
   once, exposes `identify(face_embedding) -> RecognitionResult` (`name`, `is_known: bool`,
   `confidence: float`), comparing via `face_recognition.face_distance` (or cosine distance if
   switching libraries later).
   **Hardened after user-reported misidentification bugs in multi-person live testing** (full
   root-cause writeup in `../KNOWN_ISSUES.md`): per-person distance is now the mean of the
   top-3 closest training photos (not the single min), an ambiguity margin
   (`recognition.ambiguity_margin`) rejects near-ties between two trained people instead of
   guessing, `identify_all()` enforces one-person-one-face per frame, and greetings only fire
   after the same identity is stable across consecutive recognition passes
   (`greetings.stable_recognitions`). Default threshold tightened 0.6 → 0.5 — kids' faces
   cluster much closer together than adults' under dlib's encoder.
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
    **Needs the user** — this means training on real family members' faces, which isn't
    something to automate; run `recogcore train --capture <name>` / `--build` yourself, then
    `python scripts/run_face_detection.py` to see live known/unknown labeling.
11. Tests in `tests/test_recognizer.py`: given a small fixture embeddings dict and hand-crafted
    distance values, assert `identify()` classifies known/unknown correctly at the boundary —
    this tests the classification logic, not the ML model itself.
12. Added beyond the original plan: `recogcore train --import <name> --source <path>` as an
    alternative to live capture, for training from photos the user already has. Handles Apple's
    HEIC/HEIF format (via `pillow-heif`, converted to JPEG) and downscales oversized phone photos
    (>1600px longest side) before saving, skipping any photo with no detectable face. Lands in
    the same `data/training/faces/<name>/` tree as live capture, so `--build` works unchanged.
    Tested in `tests/test_import_photos.py` with synthetic images (no real face photos needed).

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
    │   ├── test_recognizer.py
    │   └── test_import_photos.py
    └── recog_core/
        ├── cli.py                 # updated: `recogcore train --capture/--import/--build`
        └── vision/
            ├── loop.py             # updated: detect → crop → recognize → label
            ├── capture_training_photos.py
            ├── import_photos.py
            ├── embeddings.py
            └── recognizer.py
```
