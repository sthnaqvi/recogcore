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
2. Add `mediapipe` to `python-service` deps; confirm it installs cleanly under the Phase 0
   Python 3.11 venv (this is one of the reasons Phase 0 moved off Python 3.9).
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
8. Basic tests in `tests/test_face_detector.py`: feed a static test image (a small fixture image
   with a face, plus one with no face) through `detect()` and assert box count / no-crash — not
   an accuracy benchmark, just a regression guard for the wrapper code.
9. Manual verification: run the loop for ~30s in normal room lighting, confirm boxes track a
   moving face, note the FPS achieved (informs whether Phase 6 needs to worry about Pi being
   noticeably slower).

## File/folder layout created by this phase

```
python-service/
├── scripts/
│   └── run_face_detection.py
├── tests/
│   └── test_face_detector.py
│   └── fixtures/
│       ├── face_sample.jpg
│       └── no_face_sample.jpg
└── recog_core/
    └── vision/
        ├── __init__.py
        ├── face_detector.py     # BoundingBox dataclass + detector wrapper
        └── loop.py              # capture → detect → draw → (preview | headless)
```
