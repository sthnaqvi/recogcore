# RecogCore

**A stationary home-entryway assistant** — camera + mic + speaker, no motion. It recognizes
trained family members and greets them by name, greets unknown faces with a generic hello, holds
a two-way conversation, and logs every entry/exit with a snapshot. Built and verified end-to-end
on Mac first; a Raspberry Pi deployment comes later behind the same hardware abstraction layer,
so core logic never changes between the two.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Status: Phase 4 of 11](https://img.shields.io/badge/status-phase%204%20of%2011-orange)

**→ [HOW_IT_WORKS.md](HOW_IT_WORKS.md)** — a one-page, high-level breakdown of exactly which
library/model/method powers each capability (face detection, recognition, TTS, STT,
conversation), without diving into source code.

## Contents

- [How it works](HOW_IT_WORKS.md)
- [Features](#features)
- [Project status](#project-status)
- [Architecture](#architecture)
- [Setup (Mac)](#setup-mac)
- [Live face detection](#live-face-detection)
- [Training your own faces](#training-your-own-faces)
- [How recognition works, and tuning the threshold](#how-recognition-works-and-tuning-the-threshold)
- [Spoken greetings](#spoken-greetings)
- [Two-way conversation](#two-way-conversation)
- [Tests](#tests)
- [Privacy by design](#privacy-by-design)
- [Contributing](#contributing)
- [License](#license)

## Features

- Live face detection via MediaPipe, running against a Mac webcam (or Pi camera, later)
- Face recognition against your own trained family members, with a tunable known/unknown
  confidence threshold
- Train from live camera capture **or** from photos you already have — including Apple's
  HEIC/HEIF format and oversized phone photos, handled automatically
- Spoken greetings (Piper TTS) — known people get greeted by name, strangers get a generic hello,
  with a per-person cooldown so nobody gets re-greeted every frame
- Two-way conversation — listens after greeting, transcribes speech (Vosk or Whisper), and
  responds via fast rule-based intents or an optional LLM (Claude) fallback for open-ended chat
- Hardware abstraction layer (`HardwareProvider`) so the same recognition/greeting/conversation
  logic runs unchanged on a Mac during development and a Raspberry Pi in deployment
- Every person's data lives in a gitignored `data/` tree, fully separated from the codebase — see
  [Privacy by design](#privacy-by-design)

Entry/exit logging and a Pi deployment are planned next — see [Project status](#project-status)
and [PLAN.md](PLAN.md).

## Project status

This project is being built phase by phase; see [PLAN.md](PLAN.md) for the full 11-phase roadmap
and hour estimates.

| Phase | Status |
|---|---|
| 0 — Project skeleton + hardware abstraction layer | ✅ Done |
| 1 — Face detection on Mac | ✅ Done |
| 2 — Face recognition + training | ✅ Done |
| 3 — TTS / speaking | ✅ Done |
| 4 — STT + two-way conversation | ✅ Done |
| 5 — Metadata logging backend | ⬜ Not started |
| 6 — End-to-end integration + testing on Mac | ⬜ Not started |
| 7 — Optional dashboard | ⬜ Not started |
| 8 — Pi hardware setup | ⬜ Not started |
| 9 — Additional sensors | ⬜ Not started |
| 10 — Final Pi deployment + real-world testing | ⬜ Not started |

## Architecture

```
[Python Service — CV + Audio]  <--REST/localhost-->  [Node.js Backend]  -->  [MySQL]
  - Camera capture (OpenCV)                              - Log API
  - Face detection + recognition                          - Metadata storage
  - TTS (greeting)                                         - Optional dashboard
  - STT (conversation)
```

```
HardwareProvider (interface)
  ├── MacProvider    → cv2.VideoCapture(0), sounddevice, mac speaker
  └── PiProvider     → PiCamera, ReSpeaker, GPIO sensors, I2C   (Phase 8)
```

Camera, mic, and speaker are independently toggleable via config, and all recognition/greeting/
conversation/logging logic is hardware-agnostic — only the capture/output layer changes between
Mac and Pi. Full design rationale in [PLAN.md](PLAN.md).

## Setup (Mac)

Requires Python 3.10+, Node.js (for the later logging backend), and Homebrew's `cmake` (for
building `dlib`).

```bash
cd python-service
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cd ..
cp config.example.yaml config.yaml
cp .env.example .env

cd python-service
python scripts/smoke_test.py
```

`config.yaml` and `.env` are your local, gitignored copies — never commit them. See
[data/README.md](data/README.md) for where trained faces, embeddings, and other local runtime
data live (also gitignored, kept separate from this repo's code).

> Run camera/mic-touching commands from a plain Terminal window, not through a sandboxed host
> app (e.g. an IDE's built-in AI assistant) — macOS needs to grant camera/mic access directly to
> the process the first time.

## Live face detection

```bash
cd python-service
source .venv/bin/activate
./scripts/download_face_model.sh   # one-time: fetches the detection model (~230KB), not committed
python scripts/run_face_detection.py
```

## Training your own faces

Two steps, run from `python-service/` with the venv active:

1. **Get photos for each person**, either by capturing live or importing photos you already have:

   **Option A — capture live:**
   ```bash
   recogcore-train --capture <name>
   ```
   Opens the camera and waits for **SPACE** to save a shot (**q** to stop early). Aim for
   ~15–20 shots per person, varying angle and lighting — that's what makes recognition hold up
   as you actually look walking through the door, not just one lucky photo.

   **Option B — import existing photos** (e.g. photos already on your phone or computer):
   ```bash
   recogcore-train --import <name> --source /path/to/photos
   ```
   `--source` can be a single file or a directory (searched recursively). Handles:
   - **Apple's HEIC/HEIF format** (the default on iPhone) — converted to JPEG automatically.
   - **Large files** — phone photos are often 12MP+; anything over 1600px on the longest side
     is downscaled before saving, so training stays fast and `data/` stays small.
   - Any photo with **no detectable face** is skipped with a warning rather than silently
     imported, so you don't end up training on a landscape shot by mistake.

   Either way, photos land in `data/training/faces/<name>/` as normalized JPEGs, which is
   gitignored — nobody's face photos ever get committed.

2. **Build the embeddings** once everyone's captured/imported:
   ```bash
   recogcore-train --build
   ```
   Walks every `data/training/faces/<name>/` folder, generates one face embedding per photo, and
   writes them to `data/training/embeddings/known_faces.pkl` (also gitignored). Re-run this any
   time you add or recapture photos.

Then check it worked:
```bash
python scripts/run_face_detection.py
```
Trained faces show up labeled with their name in **green**; anyone else shows **orange
"Unknown."**

## How recognition works, and tuning the threshold

Each face is turned into a 128-number vector (an "embedding") that captures what that face looks
like. To recognize someone, RecogCore measures the **Euclidean distance** between the live
embedding and every embedding captured during training — the smaller the distance, the more
alike the two faces are.

`config.yaml`'s `recognition.threshold` (default **0.5**) is the cutoff: if the closest known
face is at or below this distance, it's a match; otherwise the person is labeled "Unknown."
(Distance per person is averaged over the few best-matching training photos, so one odd
training photo can't decide a match on its own.)

- **Lower threshold** (e.g. 0.45) = stricter matching. Fewer false positives (a stranger
  mistaken for family), but more false negatives (family occasionally mislabeled as Unknown,
  especially in bad lighting or extreme angles).
- **Higher threshold** (e.g. 0.6) = looser matching. Family gets recognized more reliably, but a
  stranger can occasionally get matched to a family member by mistake. Households with young
  children should stay strict — the underlying face model is trained mostly on adults, so kids'
  faces look far more alike to it than they do to you.

Two more knobs guard against misidentification:
- `recognition.ambiguity_margin` (default 0.05) — if the two closest trained people are within
  this distance of each other, RecogCore says "Unknown" rather than guessing between them.
- `greetings.stable_recognitions` (default 3) — the same identity must be seen this many
  recognition passes in a row before a greeting fires, so one misrecognized frame can't
  trigger a wrong-name greeting.

To tune it for your setup:
1. Train at least two people (`--capture` / `--build` above).
2. Run `python scripts/run_face_detection.py` and watch the confidence number next to each label
   (`confidence = 1 - distance`, so higher means a stronger match) across varied lighting and
   angles for each trained person, and for yourself as a stand-in "stranger" if no one else is
   trained yet.
3. If trained people frequently show as Unknown, raise the threshold slightly (0.6 → 0.65). If a
   stranger gets matched to a family member, lower it (0.6 → 0.55).
4. Edit `recognition.threshold` in your local `config.yaml` — not `config.example.yaml`, unless
   you're deliberately changing the shipped default for everyone who clones this repo.

## Spoken greetings

```bash
cd python-service
source .venv/bin/activate
python -m piper.download_voices en_US-lessac-medium --download-dir models/tts   # one-time, ~63MB
python scripts/run_face_detection.py
```
Recognized faces now get a spoken greeting (a random pick from `greetings.known` in
`config.yaml`, e.g. "Hi, {name}!"); unknown faces get a generic one (`greetings.unknown`). The
same person won't be re-greeted more than once per `greetings.cooldown_seconds` (default 90s).

Piper (the TTS engine) is GPL-3.0 licensed; `recog_core/audio/tts.py` invokes it as a subprocess
rather than importing it as a library, keeping a clean license boundary from this MIT repo.

## Two-way conversation

```bash
cd python-service
source .venv/bin/activate
./scripts/download_stt_model.sh   # one-time: fetches the Vosk model (~41MB), not committed
python scripts/run_conversation_demo.py
```
After the greeting, it listens for up to `conversation.listen_seconds` (default 5s), transcribes
what you said, and replies — then repeats for up to `conversation.max_turns` (default 3) or until
you stop talking. Two response modes, set via `config.yaml: conversation.mode`:

- **`rules`** (default) — a small set of keyword-matched intents (e.g. "how are you," "goodbye")
  with canned replies. Free, instant, deterministic.
- **`llm`** — falls through to Claude for anything the rules don't cover. Requires
  `ANTHROPIC_API_KEY` in your `.env` (never committed, never logged).

STT engine is set via `config.yaml: stt.engine`:
- **`vosk`** (default) — fully offline, never touches the network after the one-time model download.
- **`whisper`** — better accuracy, but downloads its model from Hugging Face Hub on first use.

## Tests

```bash
cd python-service
pytest
```

All tests use synthetic images/embeddings rather than real face photos, so the test suite itself
never needs anyone's personal data — see [Privacy by design](#privacy-by-design).

## Privacy by design

This project is meant to be cloned and trained by anyone, on their own family — so the repo
itself must never contain anyone's personal data. Concretely:

- All local/private state lives under `data/`, split into `data/training/` (captured photos +
  face embeddings — the most sensitive data in the project) and `data/runtime/` (snapshots, local
  DB files, logs). Both are gitignored entirely.
- `config.yaml` and `.env` (your real settings/secrets) are gitignored; only the placeholder
  `config.example.yaml` / `.env.example` are committed.
- ML models (face detection, TTS, STT) are fetched via download scripts at setup time, not
  committed to the repo.
- The test suite is built entirely on synthetic data (blank frames, random noise, hand-crafted
  vectors) — no real face photo has ever been or will be committed to this repo.

## Contributing

This is currently a solo hobby project built phase-by-phase per [PLAN.md](PLAN.md). Issues and
PRs are welcome once the Mac MVP (Phases 0–7) is further along.

## License

[MIT](LICENSE)
