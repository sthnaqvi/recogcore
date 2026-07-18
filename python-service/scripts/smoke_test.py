"""Manual smoke test for the HardwareProvider abstraction.

Run with the venv active, from python-service/:
    python scripts/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from recog_core.config import load_config
from recog_core.provider_factory import get_provider


def main() -> None:
    config = load_config()
    print(f"HARDWARE_MODE={config.hardware_mode}")
    provider = get_provider(config)
    provider.start()
    try:
        if provider.is_camera_enabled():
            frame = provider.get_frame()
            assert frame is not None, "camera enabled but no frame captured"
            print(f"Camera OK -- frame shape {frame.shape}")
        else:
            print("Camera disabled -- skipping")

        if provider.is_mic_enabled():
            print("Recording 1s of audio...")
            audio = provider.record_audio(1.0)
            print(f"Mic OK -- recorded {len(audio)} samples")
        else:
            print("Mic disabled -- skipping")

        if provider.is_speaker_enabled():
            print("Playing back a 440Hz test tone...")
            samplerate = 16000
            t = np.linspace(0, 0.5, int(0.5 * samplerate), endpoint=False)
            tone = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
            provider.play_audio(tone, samplerate)
            print("Speaker OK")
        else:
            print("Speaker disabled -- skipping")
    finally:
        provider.stop()


if __name__ == "__main__":
    main()
