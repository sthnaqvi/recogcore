# Phase 1 — Face detection on Mac

**Est. 6–8 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Get a live face-detection loop running against the Mac webcam through the Phase 0
`HardwareProvider` abstraction — bounding boxes drawn on a preview window, FPS measured. No
recognition (who is it) yet — just "is there a face, and where."

## Task breakdown

1. Decide the detector: MediaPipe Face Detection (fast, good for a single always-on stream,
   CPU-friendly on Mac) vs OpenCV Haar cascade (simpler, worse accuracy) vs a dlib/HOG detector
   (needed anyway from Phase 2 if using `face_recognition`). Recommendation: use MediaPipe here
   for the live loop/FPS check since it's the fastest to get bounding boxes with, and switch to
   whatever `face_recognition`/dlib gives you in Phase 2 for the actual recognition path — the
   two don't have to be the same detector.
2. Add `mediapipe` to `python-service` deps (installed under the Phase 0 Python 3.10 venv --
   already modern enough, no need for the originally-planned 3.11 bump). Note: modern mediapipe
   (0.10.x) dropped the old bundled `solutions.face_detection` API in favor of the Tasks API,
   which needs a separately-downloaded model file (`blaze_face_short_range.tflite`, ~230KB, from
   Google's official mediapipe-models storage). `scripts/download_face_model.sh` fetches it into
   `python-service/models/`, gitignored like the TTS models in Phase 3 -- not committed.
3. Write `recog_core/vision/face_detector.py`: a small class wrapping the chosen detector with
   a single method `detect(frame) -> list[BoundingBox]` (a `BoundingBox` dataclass with
   `x, y, w, h, confidence`), so Phase 2 can swap the detector implementation without touching
   callers.
4. Write `recog_core/vision/loop.py`: the capture loop — pulls frames from the
   `HardwareProvider`, runs `face_detector.detect()`, draws boxes via `cv2.rectangle` +
   confidence text, shows a preview window (`cv2.imshow`) for manual dev testing.
5. Add FPS measurement: rolling average over the last N frames, printed/overlaid on the preview
   window, so Phase 6 has a baseline to compare Pi performance against later.
6. Add a `--headless` flag/config option to run the loop without `cv2.imshow` (needed once this
   runs unattended in later phases / on Pi without a display).
7. Add a console entry point or `scripts/run_face_detection.py` for manual local testing:
   `python -m recog_core.vision.loop` opens the webcam, shows boxes, `q` to quit, prints FPS.
8. Basic tests in `tests/test_face_detector.py`: feed synthetic images (blank frame, random
   noise) through `detect()` and assert no-crash / correct return type -- deliberately *not* a
   committed real face photo fixture, since that would conflict with this project's own
   no-personal-data-in-the-repo policy. Real accuracy is checked manually (next step) instead.
9. Manual verification: run the loop for ~30s in normal room lighting, confirm boxes track a
   moving face, note the FPS achieved (informs whether Phase 6 needs to worry about Pi being
   noticeably slower).

## File/folder layout created by this phase

```
python-service/
├── scripts/
│   ├── run_face_detection.py
│   └── download_face_model.sh
├── models/                       # gitignored -- blaze_face_short_range.tflite
├── tests/
│   └── test_face_detector.py
└── recog_core/
    └── vision/
        ├── __init__.py
        ├── face_detector.py     # BoundingBox dataclass + detector wrapper
        └── loop.py              # capture → detect → draw → (preview | headless)
```
