# Phase 3 — TTS / speaking

**Est. 8–10 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Give the recognizer (Phase 2) a voice: greet a known person by name, greet an unknown person
generically, spoken aloud through the Mac speaker via the `HardwareProvider`.

## Task breakdown

1. Add `piper-tts` (offline, free, neural — per the original plan) to `python-service` deps.
   Confirm it runs on this Mac; download the chosen voice model to a models cache directory
   (not committed — see step 6).
2. Write `recog_core/audio/tts.py`: `TextToSpeech` class wrapping Piper — `synthesize(text) ->
   np.ndarray` (raw audio samples) so it composes with `HardwareProvider.play_audio()` rather
   than each caller shelling out to Piper directly.
3. Write `recog_core/greeting.py`: greeting logic — `build_greeting(recognition_result) -> str`.
   Known person → `"Hi, {name}!"` (or a small rotation of phrasings to avoid sounding robotic
   on every repeat visit); unknown → generic `"Hi there!"`. Keep phrasing templates in config
   (`config.yaml: greetings.known` / `greetings.unknown`) so they're user-editable without a
   code change.
4. Add **greeting debounce/cooldown**: don't re-greet the same recognized person every frame
   while they linger in view. Track "last greeted at" per person (in-memory, keyed by name) with
   a configurable cooldown (`config.yaml: greetings.cooldown_seconds`, e.g. 60–120s) before
   re-greeting the same person.
5. Wire the Phase 2 recognition loop: on a new (non-cooldown) recognition result, call
   `build_greeting()` → `tts.synthesize()` → `provider.play_audio()`. This should run
   asynchronously/non-blocking relative to the camera loop so speaking doesn't stall frame
   capture (a simple background thread/queue is enough at this scale).
6. Model/asset handling: Piper voice models are third-party downloads, not personal data — but
   still shouldn't bloat the git repo. Store them under a `models/` (or `data/models/`) cache
   dir, gitignored, fetched by a `scripts/download_tts_model.sh` (or first-run auto-download)
   rather than committed binary files.
7. Tests in `tests/test_greeting.py`: unit-test `build_greeting()` phrasing selection and the
   cooldown logic (using a fake clock) — these don't need real audio, just the decision logic.
8. Manual verification: run the full loop, walk in as a trained person, confirm spoken greeting
   with your name; walk in as an untrained face, confirm generic greeting; walk back and forth
   within the cooldown window, confirm no re-greet spam.

## File/folder layout created by this phase

```
python-service/
├── scripts/
│   └── download_tts_model.sh
├── tests/
│   └── test_greeting.py
└── recog_core/
    ├── greeting.py
    └── audio/
        ├── __init__.py
        └── tts.py
```
