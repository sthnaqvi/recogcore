# Known issues & improvement backlog (Phases 0–4)

A full self-review of every file written so far, from a bugs-and-improvements angle, done at the
user's request after a couple of real bugs turned up in ad-hoc testing. Kept as a living doc —
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

2. **`run_conversation_demo.py` unnecessarily opened the camera.** `MacProvider.start()` opens
   *all* hardware enabled in `config.yaml`, not just what the calling script uses — this demo is
   audio-only but was reusing the global config's `camera_enabled: true`. **Fix:** the script now
   explicitly overrides `config.camera_enabled = False` for its own run.

3. **`AsyncSpeaker`'s worker thread dies permanently on the first TTS failure.** The background
   thread that synthesizes and plays greetings had no error handling around
   `synthesize()`/`play_audio()`. Since the thread is a daemon with an unguarded `while True`
   loop, any single failure (a bad Piper invocation, a transient audio-device issue) would kill
   the thread silently — and since nothing restarts it, **every greeting for the rest of the
   process's lifetime would silently stop working**, with only a stderr traceback (easy to miss
   on a device meant to run unattended) as any indication. **Fix:** wrapped the worker body in
   `try/except`, logging the failure and continuing to the next queued item. Verified with a
   fake TTS that fails on the first call and succeeds on the second — the worker now survives
   and keeps processing.

4. **Live face detection was very laggy, reported by the user.** Root cause:
   `generate_embedding()` ran dlib's *own* HOG face detector on every already-cropped face on
   every single frame (benchmarked at ~30ms/call), on top of camera frames captured at the
   webcam's default 1920x1080. Combined with MediaPipe detection, this made the loop too slow to
   feel smooth. **Fix:** (a) pass the crop's own coordinates as `known_face_locations` to
   `face_encodings()`, skipping the redundant re-detection entirely (benchmarked: ~30ms → ~8ms,
   a 3.75x cut); (b) cap camera capture at 1280x720 via `cv2.CAP_PROP_FRAME_WIDTH/HEIGHT` rather
   than processing full 1080p every frame; (c) throttle recognition to run every 5th frame in
   `vision/loop.py`, reusing cached labels in between (detection + drawing still run every
   frame). Verified live via Terminal: even with recognition forced on *every* frame (no
   throttling), the loop now keeps up with the camera's native ~29fps at 15.9ms/frame.

5. **Greeting audio sounded distorted ("like a broken speaker"), reported by the user.** Three
   compounding causes, found and fixed one at a time as residual distortion kept surfacing after
   each fix:
   - **Sample-rate mismatch**: `MacProvider.play_audio()` played Piper's 22050Hz output straight
     through `sd.play()`, but this Mac's speakers report a native `default_samplerate` of
     **48000Hz** — forcing CoreAudio to resample on the fly on every utterance. Confirmed this
     wasn't a voice-quality issue (the user tried `en_US-hfc_female-medium`, which plays cleanly
     in Piper's own official samples, and it was still distorted in-app). **Fix:** query the
     device's native rate once, resample to match before `sd.play()`.
   - **Resampling artifacts**: the first resampling fix used plain linear interpolation
     (`np.interp`), which introduces audible harmonic artifacts on a non-integer rate ratio like
     22050→48000 (160:147) — the user reported "sounds better, but some distortion still there."
     **Fix:** switched to `scipy.signal.resample_poly` (proper anti-aliasing FIR filter).
   - **Filter-ringing overshoot**: `resample_poly`'s FIR filter can ring slightly past the valid
     [-1, 1] range on sharp transients (measured up to ~1.006 on real synthesized speech) —
     invalid PCM that can itself click. **Fix:** clip defensively after resampling. Also added an
     8ms fade-in/fade-out on every clip, since `sd.play()` opens a fresh stream per utterance and
     an abrupt silence→full-amplitude jump is a classic source of a click at the start/end of
     playback.
   All three verified via unit tests (rate-match identity, correct output length, overshoot
   clipped to exactly [-1, 1], fade ramps to zero at both edges) plus live synthesis+playback
   runs. Still **needs the user's ears** to confirm the remaining distortion is actually gone.

6. **Face recognition misidentified people badly with multiple family members trained,
   reported by the user** — one person got greeted 4 times in one session as 4 different
   identities (Tauseef, Afsha, Jazib, Unknown); two different children were labeled "Jazib"
   simultaneously in the same frame; strangers sometimes got greeted by a trained person's
   name. Five compounding root causes, all fixed:
   - **Threshold too loose for families (0.6 → 0.5 default).** The screenshot evidence: a
     toddler matched "Jazib" at distance 0.53, comfortably under 0.6. dlib's encoder is trained
     mostly on adult faces, so children's embeddings genuinely cluster close together — family
     installs (this project's whole audience) need a stricter default than dlib's canonical 0.6.
   - **No ambiguity margin.** If two trained people were both close, the classifier just picked
     whichever was closer — even by a hair. Now `recognition.ambiguity_margin` (default 0.05)
     requires the best match to beat the second-best by a clear gap, else "unknown."
   - **Single-min matching.** Per-person distance was the *minimum* across all ~18 training
     photos — one outlier photo (odd angle/lighting) could spuriously match anyone. Now the
     mean of the top-3 closest photos, so no single outlier decides.
   - **No one-person-one-face constraint.** Each detected face matched independently, so two
     faces could both be "Jazib" in the same frame. New `identify_all()` demotes all but the
     strongest match for a given name to unknown.
   - **No temporal stability.** A single misclassified frame fired a greeting instantly, and
     since the cooldown is keyed per-name, each *wrong* name was a fresh key — that's exactly
     the 4-greetings-for-one-person incident. New `GreetingStabilizer` requires the same
     identity across N consecutive recognition passes (`greetings.stable_recognitions`, default
     3) before greeting; "unknown" is held to 2× that, since it's also the fallback bucket for
     every rejected classification.
   Two adjacent bugs found and fixed during the same investigation: the perf fix from earlier
   had passed the *whole padded crop* as the face location, subtly misaligning live embeddings
   vs. training ones (now passes the tight MediaPipe box within the crop — alignment matches
   training again, speed kept); and the between-recognition-pass label cache was matched to
   boxes by list index, but the detector's box ordering can change frame to frame, so one
   person could briefly wear another's cached label (now matched by box-center proximity).
   Verified live via Terminal: 430 frames / 15s with recognition on *every* frame — 413 of 420
   identifications were the correct person, zero wrong-name flickers, and only the correct
   identity reached greeting stability. Multi-person accuracy still **needs the user** to
   verify with the actual family in frame.

7. **TTS speaking pace wasn't adjustable, reported by the user.** Piper's `--length-scale` flag
   (phoneme duration multiplier) wasn't exposed at all — pace was whatever Piper's default
   happened to be. **Fix:** added `config.yaml: tts.length_scale` (default 1.0, set to 1.15 in
   the local dev config as a starting point for slightly slower/more natural pacing), wired
   through `TextToSpeech`. Verified the flag has a real, measurable effect on output duration
   (note: Piper's synthesis has genuine run-to-run timing variance from its own noise
   parameters, so the effect is a real average shift, not a fixed exact delta per utterance).

## P2 — real issues, worth addressing soon

1. **Piper subprocess call has no timeout.** `TextToSpeech.synthesize()` calls `subprocess.run()`
   without `timeout=`. The P1 error-handling fix above handles *fast failures* (non-zero exit,
   bad input), but if the Piper process ever hangs (resource contention, a stuck subprocess), the
   call blocks forever and the exception handler never gets a chance to run — the worker thread
   would be stuck, not crashed, which is arguably worse (no error printed at all). No evidence
   this happens in practice (every real run completed in ~200-300ms), but worth adding
   `timeout=30` (or similar) as defense-in-depth.

2. **`known_faces.pkl` uses `pickle`.** `pickle.load()` executes arbitrary code if the file's
   contents are ever untrusted. Today this is low-risk — the file is always generated locally by
   the user's own `recogcore-train --build`, never fetched from a network or another user — but
   it's a latent footgun in a project that otherwise cares a lot about safety/privacy (e.g. if
   the open-source project ever grows a "share your trained model" feature, or a user copies a
   `known_faces.pkl` from somewhere else without thinking about it). Worth switching to a safer
   format (`.npz`, or JSON + base64) before that ever becomes possible.

3. **Stale plan docs from before the Python-version and data-layout deviations.**
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

4. **No CI.** Tests exist (46 passing) but nothing runs them automatically on push/PR — a
   `.github/workflows/test.yml` running `pytest` would be a reasonable, cheap addition for a
   public repo, and would have caught the `test_face_detector.py` fresh-clone failure (P1 #1)
   automatically.

5. **No cost/rate guard on `conversation.mode: llm`.** Every conversation turn (up to
   `max_turns`) makes a real Anthropic API call with no cap on how many conversations can happen
   per hour/day. `rules` is the default and the greeting cooldown throttles new conversations
   somewhat, but if `llm` mode is ever made the default, an unattended device repeatedly
   triggering paid API calls with no ceiling is a real cost risk worth guarding before then.

6. **Camera resolution/recognition-throttle interval are hardcoded**, not config-driven
   (`MacProvider`'s `camera_width`/`camera_height` defaults, `RECOGNITION_EVERY_N_FRAMES` in
   `vision/loop.py`). Fine as sensible defaults today; worth exposing via `config.yaml` if the
   right values turn out to differ meaningfully on the Pi (Phase 8) or for other users' hardware.

## P3 — nice-to-have / forward-looking

1. **Dependency footprint is heavy and monolithic.** `pyproject.toml` has one flat dependency
   list — `mediapipe`, `dlib`, `face_recognition`, `vosk`, `faster-whisper`, `piper-tts`,
   `anthropic`, `Pillow`, `pillow-heif`, `scipy`, all always installed together. Splitting into optional
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
