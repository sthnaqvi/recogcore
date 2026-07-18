# Phase 0 — Project skeleton + hardware abstraction layer

**Est. 8–10 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Stand up the repo structure, a working modern-Python environment, and the `HardwareProvider`
abstraction (with a Mac implementation) that every later phase builds on. Nothing here does
face recognition or audio processing yet — it just proves camera/mic/speaker can be opened and
released cleanly through the abstraction, with config-driven enable/disable per module.

## Task breakdown

1. **Fix the Python version problem.** System Python is 3.9.6 (macOS CLT python) — too old/finicky
   for `dlib`/`face_recognition`/`mediapipe` wheels used from Phase 1 onward. Install Python 3.11
   via `pyenv install 3.11` (or `brew install python@3.11`), and set it as the project-local
   version (`pyenv local 3.11` inside `python-service/`).
2. Create the repo root layout (below) and initialize git (`git init`, initial `.gitignore`).
3. Create `python-service/` as an installable package: `pyproject.toml` with project metadata,
   a `recog_core` package dir, and console-script entry points (`recogcore-run`, `recogcore-train` —
   the latter wired up for real in Phase 2).
4. Create and activate the venv inside `python-service/` (`python3.11 -m venv .venv`), add a
   `requirements.txt` (or rely on `pyproject.toml` deps) with the baseline deps needed even for
   the skeleton: `opencv-python`, `sounddevice`, `pyyaml`, `python-dotenv`, `fastapi`/`flask` +
   `uvicorn` (whichever is chosen for the later local REST server), `pytest`.
5. Design the `HardwareProvider` abstract interface in `recog_core/hardware/base.py`: an ABC (or
   `Protocol`) defining `get_frame() -> np.ndarray | None`, `record_audio(seconds) -> np.ndarray`,
   `play_audio(samples)`, `start()/stop()` lifecycle, and per-module `is_camera_enabled() /
   is_mic_enabled() / is_speaker_enabled()` gates.
6. Implement `MacProvider(HardwareProvider)` in `recog_core/hardware/mac_provider.py`:
   `cv2.VideoCapture(0)` for camera, `sounddevice` for mic input, and system speaker output
   (start with `sounddevice`/`afplay`-based playback so no extra dep is needed).
7. Implement a `NullProvider` (or per-module null objects) so camera/mic/speaker can each be
   individually disabled via config without special-casing call sites — every call site just
   asks the provider, which no-ops if that module is off.
8. Build `recog_core/config.py`: loads `config.yaml` (falls back to `config.example.yaml` if
   local file absent) + `.env` via `python-dotenv`; exposes `HARDWARE_MODE` (`mac`/`pi`),
   `CAMERA_ENABLED`, `MIC_ENABLED`, `SPEAKER_ENABLED`, and a `data_dir` path resolver.
9. Build a tiny `recog_core/provider_factory.py`: `get_provider(config) -> HardwareProvider`
   that returns `MacProvider` when `HARDWARE_MODE=mac` (raises `NotImplementedError` for `pi`
   until Phase 8).
10. Write a manual smoke-test script (`scripts/smoke_test.py` or a `pytest` test using
    `pytest-mock`/manual run flag) that: opens the Mac camera via the provider, grabs one frame,
    confirms it's non-empty, records 1s of audio, plays back a short test tone, then releases
    everything cleanly. This is the "does the abstraction actually work" check for this phase.
11. `data/` scaffolding already exists (set up ahead of this phase): `data/training/`
    (`faces/<person>/`, `embeddings/`) for personal training data, and `data/runtime/`
    (`snapshots/`, `db/`, `logs/`) for disposable generated state — both fully gitignored, with
    `data/README.md` (committed) documenting the split. The real `config.yaml` lives at the repo
    root next to the committed `config.example.yaml`, not under `data/`.
12. Write root `README.md`: what the project is, install steps (`pyenv`/`venv` setup, `pip
    install -e python-service/`), how `config.example.yaml` → `config.yaml` copy works, and a
    link to `PLAN.md` for the roadmap.
13. `.gitignore` already exists at the repo root, covering: `data/training/`, `data/runtime/`,
    `config.yaml`, `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `node_modules/`, `.DS_Store`,
    `*.log` — only `config.example.yaml`/`.env.example` and code are committed.

## File/folder layout created by this phase

```
robot-assistant/
├── PLAN.md
├── README.md
├── .gitignore                     # already in place
├── config.example.yaml
├── plan/
│   └── (phase docs)
├── data/                          # already in place — see data/README.md
│   ├── README.md
│   ├── training/                  # gitignored — faces/, embeddings/
│   └── runtime/                   # gitignored — snapshots/, db/, logs/
└── python-service/
    ├── pyproject.toml
    ├── requirements.txt
    ├── .venv/                     # gitignored, created locally not committed
    ├── scripts/
    │   └── smoke_test.py
    ├── tests/
    │   └── test_hardware_provider.py
    └── recog_core/
        ├── __init__.py
        ├── config.py
        ├── provider_factory.py
        └── hardware/
            ├── __init__.py
            ├── base.py            # HardwareProvider ABC
            ├── mac_provider.py
            └── null_provider.py
```
