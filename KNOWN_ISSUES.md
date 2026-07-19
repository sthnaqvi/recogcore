# Known issues & improvement backlog (Phases 0–4)

A full self-review of every file written so far, from a bugs-and-improvements angle, done at the
user's request after a couple of real bugs turned up in ad-hoc testing (the demo script
unnecessarily opening the camera; see [P1 items](#p1--fixed-now) below). Kept as a living doc —
update it as new phases land or items get resolved.

**Priority key:** P1 = actively broken for someone using the code today, fixed immediately. P2 =
real issue, no urgent user-facing impact, worth fixing soon. P3 = nice-to-have / forward-looking,
relevant mainly once later phases (5–10) build on top of this code.

## P1 — fixed now

1. **`tests/test_face_detector.py` hard-fails on a fresh clone.** The `detector` fixture
   instantiated a real `FaceDetector()`, which requires `models/blaze_face_short_range.tflite` —
   a file only created by running `scripts/download_face_model.sh`, never by `pip install`.
   Anyone following the README's plain `pytest` instructions on a fresh clone would hit 2 hard
   `FileNotFoundError` test failures with no explanation. **Fix:** the fixture now checks for the
   model file and calls `pytest.skip()` with a clear message if it's missing, instead of failing.
   Verified both paths (skips cleanly without the model, passes fully with it).

2. **`AsyncSpeaker`'s worker thread dies permanently on the first TTS failure.** The background
   thread that synthesizes and plays greetings had no error handling around
   `synthesize()`/`play_audio()`. Since the thread is a daemon with an unguarded `while True`
   loop, any single failure (a bad Piper invocation, a transient audio-device issue) would kill
   the thread silently — and since nothing restarts it, **every greeting for the rest of the
   process's lifetime would silently stop working**, with only a stderr traceback (easy to miss
   on a device meant to run unattended) as any indication. **Fix:** wrapped the worker body in
   `try/except`, logging the failure and continuing to the next queued item. Verified with a
   fake TTS that fails on the first call and succeeds on the second — the worker now survives
   and keeps processing.

## P2 — real issues, worth addressing soon

1. **Piper subprocess call has no timeout.** `TextToSpeech.synthesize()` calls `subprocess.run()`
   without `timeout=`. The P1 fix above handles *fast failures* (non-zero exit, bad input), but
   if the Piper process ever hangs (resource contention, a stuck subprocess), the call blocks
   forever and the P1 exception handler never gets a chance to run — the worker thread would be
   stuck, not crashed, which is arguably worse (no error printed at all). No evidence this
   happens in practice (every real run completed in ~200-300ms), but worth adding
   `timeout=30` (or similar) as defense-in-depth.

2. **Double face-detection in the recognition path.** `generate_embedding()`
   (`recog_core/vision/embeddings.py`) calls `face_recognition.face_encodings(rgb)` *without*
   passing `known_face_locations` — meaning it re-runs dlib's own HOG face detector on a crop
   MediaPipe already found a face in. This is redundant work every frame, and worse, dlib's HOG
   detector can disagree with MediaPipe on tight/rotated crops and silently find nothing (the
   function returns `None`, which the caller already handles, but the face just never gets
   labeled that frame with no visible reason why). Passing an explicit bounding box derived from
   the MediaPipe detection would skip the redundant re-detection and remove this failure mode.
   Not yet observed as a real problem in live testing, but a plausible source of "sometimes it
   just doesn't recognize me for a frame or two" flakiness.

3. **`known_faces.pkl` uses `pickle`.** `pickle.load()` executes arbitrary code if the file's
   contents are ever untrusted. Today this is low-risk — the file is always generated locally by
   the user's own `recogcore-train --build`, never fetched from a network or another user — but
   it's a latent footgun in a project that otherwise cares a lot about safety/privacy (e.g. if
   the open-source project ever grows a "share your trained model" feature, or a user copies a
   `known_faces.pkl` from somewhere else without thinking about it). Worth switching to a safer
   format (`.npz`, or JSON + base64) before that ever becomes possible.

4. **Stale plan docs from before the Python-version and data-layout deviations.**
   - `plan/phase-0-skeleton.md` step 1 still says to install Python 3.11 via `pyenv` — the repo
     actually ended up on Python 3.10 (already installed via Homebrew, no `pyenv` involved) and
     nothing in that file corrects it.
   - `plan/phase-8-pi-hardware.md` step 3 says "Python 3.11 (via `pyenv` same as Phase 0...)" —
     doubly wrong now, since Phase 0 used neither `pyenv` nor 3.11.
   - `plan/phase-7-dashboard.md` still references `data/snapshots/` instead of
     `data/runtime/snapshots/` (the `training/`/`runtime/` split was introduced after this doc
     was first written, and phase-7 wasn't updated like phases 0/2/5 were).
   These are docs for *unbuilt* phases (7, 8) or a stale historical note (0) — no running code is
   affected, but whoever picks up those phases next (including a future session reading these
   docs for context) would get misled.

5. **No CI.** Tests exist (43 passing) but nothing runs them automatically on push/PR — a
   `.github/workflows/test.yml` running `pytest` would be a reasonable, cheap addition for a
   public repo, and would have caught the `test_face_detector.py` fresh-clone failure (P1 #1)
   automatically.

6. **No cost/rate guard on `conversation.mode: llm`.** Every conversation turn (up to
   `max_turns`) makes a real Anthropic API call with no cap on how many conversations can happen
   per hour/day. `rules` is the default and the greeting cooldown throttles new conversations
   somewhat, but if `llm` mode is ever made the default, an unattended device repeatedly
   triggering paid API calls with no ceiling is a real cost risk worth guarding before then.

## P3 — nice-to-have / forward-looking

1. **Dependency footprint is heavy and monolithic.** `pyproject.toml` has one flat dependency
   list — `mediapipe`, `dlib`, `face_recognition`, `vosk`, `faster-whisper`, `piper-tts`,
   `anthropic`, `Pillow`, `pillow-heif`, all always installed together. Splitting into optional
   extras (e.g. `[vision]`, `[audio]`, `[llm]`) would let a resource-constrained Pi (Phase 8)
   install only what it needs — directly relevant to phase-8's own stated concern about the Pi
   being slower and possibly needing lighter models.
2. **LLM model is hardcoded** (`DEFAULT_MODEL` in `llm_responder.py`) rather than config-driven,
   inconsistent with how everything else (threshold, greetings, STT engine, conversation mode)
   is exposed via `config.yaml`. Low impact, easy to add (`conversation.llm_model`) later.
3. **Config-mutation pattern is ad hoc.** The camera-disable fix in `run_conversation_demo.py`
   mutates a loaded `Config` instance directly (`config.camera_enabled = False`). Works fine
   since `Config` isn't frozen, but a cleaner pattern (e.g. `dataclasses.replace(config, ...)`,
   or an explicit override parameter on `get_provider`) would make per-script hardware overrides
   more discoverable/consistent if more scripts need this later.
4. **`AsyncSpeaker`'s queue is unbounded and un-prioritized.** If several different people trigger
   greetings in quick succession, each greeting plays fully before the next starts — someone
   could hear a greeting several seconds after walking away, seemingly desynced from who's
   actually in front of the camera by then. Not a problem yet (single-person testing so far),
   but worth reconsidering once Phase 6 handles multiple people in frame.
5. **`GreetingCooldown`/`AsyncSpeaker` aren't designed for concurrent multi-person conversations.**
   Fine for the current single-greeting-at-a-time use case; Phase 6 ("process the
   largest/closest face for conversation... but still log every recognized face") will need to
   think about this explicitly.
6. **`WhisperSTT` reloads its model on every `get_stt("whisper")` call** with no caching. Not an
   issue today (every script instantiates it once at startup), but would be a real per-visit
   latency cost if Phase 6 ends up creating a fresh STT instance per conversation instead of
   once per process.
7. **`Recognizer.identify()` has no defensive check on embedding shape/dimensionality** — would
   raise inside `face_recognition.face_distance` if ever given a malformed embedding. Low risk
   since embeddings are always generated by the same encoder internally, but worth a guard if
   this ever becomes a public-facing API surface.
