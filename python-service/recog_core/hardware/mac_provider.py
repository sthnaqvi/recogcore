from __future__ import annotations

import cv2
import numpy as np
import sounddevice as sd

from .base import HardwareProvider

DEFAULT_SAMPLERATE = 16000


class MacProvider(HardwareProvider):
    """Camera via OpenCV, mic/speaker via sounddevice (PortAudio)."""

    def __init__(
        self,
        camera_enabled: bool = True,
        mic_enabled: bool = True,
        speaker_enabled: bool = True,
        camera_index: int = 0,
    ) -> None:
        self._camera_enabled = camera_enabled
        self._mic_enabled = mic_enabled
        self._speaker_enabled = speaker_enabled
        self._camera_index = camera_index
        self._cap: cv2.VideoCapture | None = None

    def start(self) -> None:
        if self._camera_enabled:
            self._cap = cv2.VideoCapture(self._camera_index)
            if not self._cap.isOpened():
                raise RuntimeError(f"Could not open Mac camera at index {self._camera_index}")

    def stop(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def is_camera_enabled(self) -> bool:
        return self._camera_enabled

    def is_mic_enabled(self) -> bool:
        return self._mic_enabled

    def is_speaker_enabled(self) -> bool:
        return self._speaker_enabled

    def get_frame(self) -> np.ndarray | None:
        if not self._camera_enabled or self._cap is None:
            return None
        ok, frame = self._cap.read()
        return frame if ok else None

    def record_audio(self, seconds: float) -> np.ndarray:
        if not self._mic_enabled:
            return np.array([], dtype=np.float32)
        recording = sd.rec(
            int(seconds * DEFAULT_SAMPLERATE),
            samplerate=DEFAULT_SAMPLERATE,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        return recording.flatten()

    def play_audio(self, samples: np.ndarray, samplerate: int = DEFAULT_SAMPLERATE) -> None:
        if not self._speaker_enabled:
            return
        sd.play(samples, samplerate)
        sd.wait()
