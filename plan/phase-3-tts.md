# Phase 3 — TTS / speaking

**Est. 8–10 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Give the recognizer (Phase 2) a voice: greet a known person by name, greet an unknown person
generically, spoken aloud through the Mac speaker via the `HardwareProvider`.

## Task breakdown

1. Add `piper-tts` (offline, free, neural — per the original plan) to `python-service` deps.
   Confirmed it runs on this Mac; downloaded the `en_US-lessac-medium` voice (~63MB) via Piper's
   built-in `python -m piper.download_voices` helper into `models/tts/` (gitignored). Note:
   `piper-tts` itself is GPL-3.0-licensed -- since this repo is MIT, `tts.py` invokes it via
   `subprocess` (like calling `ffmpeg`) rather than `import piper` directly, keeping a clean
   license boundary instead of linking a GPL library into an MIT codebase.
2. Write `recog_core/audio/tts.py`: `TextToSpeech` class wrapping the Piper CLI subprocess --
   `synthesize(text) -> np.ndarray` (raw float32 PCM via `--output-raw`) so it composes with
   `HardwareProvider.play_audio()` rather than each caller shelling out to Piper directly. Also
   adds `AsyncSpeaker`: a single background worker thread + queue so greeting synthesis/playback
   never blocks the camera loop and multiple greetings never overlap each other (this is the
   "background thread/queue" from step 5, implemented alongside the TTS wrapper itself).
   **Updated after user reports of distorted, wrong-speed playback** (full root-cause writeup in
   `../KNOWN_ISSUES.md`): added `length_scale` (Piper's phoneme-duration control) as a
   `config.yaml: tts.length_scale` setting so pacing is tunable without a code change, and fixed
   three compounding audio-quality bugs in `MacProvider.play_audio()` (Phase 0's file) --
   playback at the wrong sample rate, a crude resampling method, and unclipped filter-ringing
   overshoot. The TTS synthesis itself was never the problem; every fix was in how the resulting
   audio got played back.
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
├── models/
│   └── tts/                      # gitignored -- en_US-lessac-medium.onnx (+ .json config)
├── tests/
│   └── test_greeting.py
└── recog_core/
    ├── config.py                  # updated: greetings.known/unknown/cooldown_seconds
    ├── greeting.py                 # build_greeting() + GreetingCooldown
    ├── audio/
    │   ├── __init__.py
    │   └── tts.py                  # TextToSpeech + AsyncSpeaker
    └── vision/
        └── loop.py                 # updated: recognize → cooldown check → speak
```
