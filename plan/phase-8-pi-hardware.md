# Phase 8 — Pi hardware setup

**Est. 15–20 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Move the Mac MVP (Phases 0–7) onto a Raspberry Pi. The entire point of the Phase 0
`HardwareProvider` abstraction is that this phase adds a new provider and swaps a config flag —
**no changes to recognition/greeting/conversation/logging logic.** If this phase requires editing
core logic, that's a signal the abstraction leaked somewhere in Phases 0–6 and should be fixed
rather than worked around.

## Task breakdown

1. Flash Pi OS (64-bit, Raspberry Pi OS Lite if headless) to the SD card; initial boot config
   (hostname, SSH enabled, Wi-Fi/network).
2. Physical hardware setup: attach Pi Camera Module (or USB webcam), ReSpeaker/USB mic, small
   speaker; confirm each is detected at the OS level (`libcamera-hello`/`v4l2-ctl` for camera,
   `arecord -l`/`aplay -l` for audio) before writing any Python code against them.
3. Install system dependencies on the Pi: Python 3.11 (via `pyenv` same as Phase 0, or the
   distro package if new enough), `cmake`/build tools for `dlib`, audio libs (`portaudio` for
   `sounddevice`), `libcamera` bindings if using the Pi Camera Module rather than a USB webcam.
4. Clone the repo onto the Pi, set up the `python-service` venv identically to Phase 0's Mac
   setup — this is where the "one command to onboard" install flow designed in Phase 0 either
   proves itself or needs fixing.
5. Implement `PiProvider(HardwareProvider)` in `recog_core/hardware/pi_provider.py`, matching
   the exact interface `MacProvider` implements (`get_frame`, `record_audio`, `play_audio`,
   `start`/`stop`): camera via `picamera2` (or `cv2.VideoCapture` if using a USB webcam), mic/
   speaker via `sounddevice` (ReSpeaker should work through the same PortAudio backend as Mac)
   or ALSA directly if `sounddevice` has issues on Pi.
6. Update `provider_factory.py` (Phase 0) to actually return `PiProvider` when
   `HARDWARE_MODE=pi` (currently raises `NotImplementedError`).
7. Run the Phase 0 smoke test script on the Pi against `PiProvider` first — prove camera/mic/
   speaker work through the abstraction before attempting the full recognition pipeline.
8. **Performance tuning** — the Pi is slower than the Mac dev machine used for Phases 1–6:
   - Benchmark FPS with the existing MediaPipe detector (Phase 1) on Pi; if too slow, consider
     lowering capture resolution or frame-processing rate (process every Nth frame) via config,
     not a code fork.
   - Benchmark `face_recognition`/dlib recognition (Phase 2) on Pi; if too slow, evaluate
     switching to a lighter model (e.g. MobileFaceNet) behind the same `Recognizer` interface —
     this is exactly the kind of swap the Phase 2 abstraction should already support without
     touching callers.
   - Benchmark STT (Phase 4): Vosk is likely the only realistic option on Pi (Whisper is heavy);
     confirm the `stt.engine` config flag makes this a config change, not code change, when
     moving from Mac to Pi.
9. Re-run the Phase 6 edge-case tests (multiple faces, poor lighting, config toggles) on the Pi
   specifically, since Pi camera/mic characteristics differ from the Mac's built-in hardware.
10. Document Pi-specific setup steps in `docs/pi-setup.md` (flashing, physical wiring, driver
    quirks encountered) so this phase is repeatable for anyone else building a Pi unit.

## File/folder layout created by this phase

```
robot-assistant/
└── docs/
    └── pi-setup.md

python-service/
└── recog_core/
    └── hardware/
        └── pi_provider.py
```
