from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class HardwareProvider(ABC):
    """Abstraction over camera/mic/speaker I/O so core logic never touches hardware directly.

    MacProvider and PiProvider are swapped via config (`HARDWARE_MODE`) without any change to
    the recognition/greeting/conversation/logging code that consumes this interface.
    """

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def is_camera_enabled(self) -> bool: ...

    @abstractmethod
    def is_mic_enabled(self) -> bool: ...

    @abstractmethod
    def is_speaker_enabled(self) -> bool: ...

    @abstractmethod
    def get_frame(self) -> np.ndarray | None:
        """Latest camera frame (BGR, OpenCV convention), or None if camera is disabled/unavailable."""

    @abstractmethod
    def record_audio(self, seconds: float) -> np.ndarray:
        """Record `seconds` of mono audio as a 1-D float32 array. Empty array if mic disabled."""

    @abstractmethod
    def play_audio(self, samples: np.ndarray, samplerate: int) -> None:
        """Play `samples` through the speaker. No-op if speaker disabled."""
