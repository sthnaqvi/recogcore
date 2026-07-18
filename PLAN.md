# RecogCore — Home Robot Assistant — Project Plan

> Project name: **RecogCore** — the recognition engine at the center of the system (Python
> package: `recog_core`; CLI: `recogcore`).

## Goal

A stationary (no motion) home assistant: camera + mic + speaker only.
- Detects and recognizes trained family members, greets them personally
- Greets unknown/stranger faces with a generic "Hi"
- Two-way conversation (STT + response + TTS)
- Logs every person's entry/exit with metadata (name, confidence, timestamp, event type, snapshot)

Built and tested end-to-end on Mac first. Pi (+ camera/mic/speaker + motion/temp sensors) added
later, swapped in via a hardware abstraction layer — core logic never changes between Mac and Pi.

## Open-source design constraint

This project is meant to be public: anyone can clone it, install it, train it on **their own**
family's faces, and run it. That means the repo itself must never contain anyone's personal data
(photos, embeddings, real config values, local DB dumps). Concretely:

- Local/private state lives under `data/`, split into two gitignored subtrees:
  `data/training/` (your family's captured photos + generated face embeddings — the most
  sensitive data in the project) and `data/runtime/` (snapshots, local DB files/dumps, logs —
  disposable/regeneratable). [data/README.md](data/README.md) (checked in) documents the layout.
- The real `config.yaml` and `.env` live at the repo root, gitignored, alongside the committed
  `config.example.yaml` / `.env.example` placeholders — kept at the root rather than under
  `data/` so the real and example files are easy to diff side by side.
- Default DB migrations (e.g. [backend/migrations/001_create_person_events.sql](backend/migrations/001_create_person_events.sql))
  are always committed — schema is code, not private data.
- The Python service and Node backend are each structured as installable, importable packages
  (`pyproject.toml`, `package.json`) with CLI entry points, so onboarding a new user is:
  `pip install -e .` / `npm install`, copy the example config, run a `train` command against
  their own photos, then `run`.
- No pretrained face-image datasets or third-party face photos are ever committed — only code,
  model *download* scripts/config (models fetched at install/first-run time), and docs.

## Architecture

```
[Python Service — CV + Audio]  <--REST/localhost-->  [Node.js Backend]  -->  [MySQL]
  - Camera capture (OpenCV)                              - Log API
  - Face detection + recognition                          - Metadata storage
  - TTS (greeting)                                         - Optional dashboard
  - STT (conversation)
```

### Hardware abstraction (core design decision)

```
HardwareProvider (interface)
  ├── MacProvider    → cv2.VideoCapture(0), sounddevice, mac speaker
  └── PiProvider     → PiCamera, ReSpeaker, GPIO sensors, I2C
```

- Switch via config: `HARDWARE_MODE=mac | pi`
- Camera / mic / speaker independently toggleable via config flags, for isolated testing
- All recognition/TTS/STT/logging logic is hardware-agnostic — only the capture/output layer
  changes between Mac and Pi

### Tech stack
- **CV + Audio**: Python (OpenCV, face_recognition / MediaPipe, Piper TTS, Vosk/Whisper STT)
- **Backend**: Node.js + MySQL (metadata logging, optional dashboard)
- **Communication**: local REST calls between Python service and Node backend

### Environment notes (confirmed on this Mac)
- System Python is 3.9.6 (macOS Command Line Tools Python) — **do not build on this**. Phase 0
  installs a modern Python (3.11+) via `pyenv` or `brew`, isolated in a project venv, because
  `dlib`/`face_recognition`/`mediapipe` wheel availability is version-sensitive.
- Node v24.14.1, npm 11.11.0, MySQL 8.0.45 already available via Homebrew — no setup needed there
  beyond creating the project's own database/user.

## Phases

Each phase now has its own in-depth doc under `plan/` with a concrete, ordered task breakdown and
the exact file/folder layout it creates. This top-level file stays a scannable index; sub-phase
ticket breakdown will be added inside each phase's own file in a later pass.

| Phase | Doc | Est. Hours |
|---|---|---|
| 0 — Project skeleton + hardware abstraction layer | [plan/phase-0-skeleton.md](plan/phase-0-skeleton.md) | 8–10 |
| 1 — Face detection on Mac | [plan/phase-1-face-detection.md](plan/phase-1-face-detection.md) | 6–8 |
| 2 — Face recognition + training | [plan/phase-2-face-recognition.md](plan/phase-2-face-recognition.md) | 15–20 |
| 3 — TTS / speaking | [plan/phase-3-tts.md](plan/phase-3-tts.md) | 8–10 |
| 4 — STT + two-way conversation | [plan/phase-4-stt-conversation.md](plan/phase-4-stt-conversation.md) | 20–30 |
| 5 — Metadata logging backend | [plan/phase-5-logging-backend.md](plan/phase-5-logging-backend.md) | 12–15 |
| 6 — End-to-end integration + testing on Mac | [plan/phase-6-integration-testing.md](plan/phase-6-integration-testing.md) | 15–20 |
| 7 — Optional dashboard | [plan/phase-7-dashboard.md](plan/phase-7-dashboard.md) | 10–15 |
| **— MVP complete on Mac here (~85–115 hrs) —** | | |
| 8 — Pi hardware setup | [plan/phase-8-pi-hardware.md](plan/phase-8-pi-hardware.md) | 15–20 |
| 9 — Additional sensors | [plan/phase-9-sensors.md](plan/phase-9-sensors.md) | 12–18 |
| 10 — Final Pi deployment + real-world testing | [plan/phase-10-deployment.md](plan/phase-10-deployment.md) | 10–15 |

## Totals

| Stage | Hours |
|---|---|
| Mac MVP (Phase 0–7) | ~85–115 hrs |
| Pi migration + sensors (Phase 8–10) | ~37–53 hrs |
| **Grand total** | **~120–170 hrs** |

## Hardware cost (Pi stage)

| Item | Approx Cost (INR) |
|---|---|
| Raspberry Pi 4/5 (4GB) | ₹5,000–6,500 |
| Pi Camera Module / USB webcam | ₹1,200–2,500 |
| USB mic / ReSpeaker 2-mic HAT | ₹500–2,000 |
| Small speaker | ₹500–1,000 |
| 32GB MicroSD card | ₹400 |
| Power adapter (5V/3A) | ₹500 |
| Case/mounting (DIY) | ₹300–500 |
| Motion + temp sensors (Phase 9) | ₹300–800 |
| **Total** | **~₹8,800–14,300** |

## Progress Log
_(Update this section as phases are completed — Claude Code reads this file at the start of every session for context.)_

- [x] Phase 0 — [plan/phase-0-skeleton.md](plan/phase-0-skeleton.md) (branch: `hardware-abstraction-bootstrap`; camera/mic/speaker + config toggles verified on Mac)
- [ ] Phase 1 — [plan/phase-1-face-detection.md](plan/phase-1-face-detection.md)
- [ ] Phase 2 — [plan/phase-2-face-recognition.md](plan/phase-2-face-recognition.md)
- [ ] Phase 3 — [plan/phase-3-tts.md](plan/phase-3-tts.md)
- [ ] Phase 4 — [plan/phase-4-stt-conversation.md](plan/phase-4-stt-conversation.md)
- [ ] Phase 5 — [plan/phase-5-logging-backend.md](plan/phase-5-logging-backend.md)
- [ ] Phase 6 — [plan/phase-6-integration-testing.md](plan/phase-6-integration-testing.md)
- [ ] Phase 7 — [plan/phase-7-dashboard.md](plan/phase-7-dashboard.md)
- [ ] Phase 8 — [plan/phase-8-pi-hardware.md](plan/phase-8-pi-hardware.md)
- [ ] Phase 9 — [plan/phase-9-sensors.md](plan/phase-9-sensors.md)
- [ ] Phase 10 — [plan/phase-10-deployment.md](plan/phase-10-deployment.md)
