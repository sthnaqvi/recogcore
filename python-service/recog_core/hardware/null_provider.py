from __future__ import annotations

import numpy as np

from .base import HardwareProvider


class NullProvider(HardwareProvider):
    """No-op provider — every module reports disabled. Used in tests and when a HardwareProvider
    is needed but no real camera/mic/speaker should ever be touched."""

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def is_camera_enabled(self) -> bool:
        return False

    def is_mic_enabled(self) -> bool:
        return False

    def is_speaker_enabled(self) -> bool:
        return False

    def get_frame(self) -> np.ndarray | None:
        return None

    def record_audio(self, seconds: float) -> np.ndarray:
        return np.array([], dtype=np.float32)

    def play_audio(self, samples: np.ndarray, samplerate: int = 16000) -> None:
        pass
