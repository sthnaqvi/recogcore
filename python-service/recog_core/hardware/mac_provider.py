from __future__ import annotations

from math import gcd

import cv2
import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly

from .base import HardwareProvider

DEFAULT_SAMPLERATE = 16000


def _resample(samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Polyphase resample with a proper anti-aliasing filter (scipy.signal.resample_poly) --
    plain linear interpolation (an earlier version of this function) introduces audible harmonic
    artifacts on non-integer rate ratios like 22050->48000 (a 160:147 ratio), which is exactly
    the TTS-output-rate -> speaker-native-rate conversion this function is used for.

    FIR-filter ringing can push the resampled signal slightly outside [-1, 1] (observed up to
    ~1.006 on real Piper output) -- clipped defensively since anything beyond that range is
    invalid PCM and can itself cause audible clicks."""
    if orig_sr == target_sr or len(samples) == 0:
        return samples
    factor = gcd(orig_sr, target_sr)
    up, down = target_sr // factor, orig_sr // factor
    resampled = resample_poly(samples, up, down).astype(np.float32)
    return np.clip(resampled, -1.0, 1.0)


def _fade_edges(samples: np.ndarray, samplerate: int, fade_ms: float = 8.0) -> np.ndarray:
    """Ramps the first/last few milliseconds to/from silence. Every `sd.play()` call opens a
    fresh audio stream; without this, the hardware's abrupt jump from silence to full amplitude
    (and back) is a classic source of an audible click/pop at the start and end of playback."""
    fade_samples = min(int(samplerate * fade_ms / 1000), len(samples) // 2)
    if fade_samples <= 0:
        return samples
    samples = samples.copy()
    ramp = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
    samples[:fade_samples] *= ramp
    samples[-fade_samples:] *= ramp[::-1]
    return samples


class MacProvider(HardwareProvider):
    """Camera via OpenCV, mic/speaker via sounddevice (PortAudio)."""

    def __init__(
        self,
        camera_enabled: bool = True,
        mic_enabled: bool = True,
        speaker_enabled: bool = True,
        camera_index: int = 0,
        camera_width: int = 1280,
        camera_height: int = 720,
    ) -> None:
        self._camera_enabled = camera_enabled
        self._mic_enabled = mic_enabled
        self._speaker_enabled = speaker_enabled
        self._camera_index = camera_index
        self._camera_width = camera_width
        self._camera_height = camera_height
        self._cap: cv2.VideoCapture | None = None
        self._output_samplerate: int | None = None

    def start(self) -> None:
        if self._camera_enabled:
            self._cap = cv2.VideoCapture(self._camera_index)
            if not self._cap.isOpened():
                raise RuntimeError(f"Could not open Mac camera at index {self._camera_index}")
            # Many Mac webcams default to 1080p+; capping resolution here (rather than
            # downscaling every frame after capture) cuts detection + face-encoding cost
            # substantially, since both scale with pixel count. 720p is still plenty sharp
            # for a stationary entryway camera.
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._camera_width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._camera_height)

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
        # Playing at a rate the output device doesn't natively support (e.g. TTS's 22050Hz on
        # speakers that default to 48000Hz) forces CoreAudio to resample on the fly on every
        # single call, which is a common source of crackly/distorted-sounding playback. Resample
        # to the device's own native rate ourselves instead, once, before handing it off.
        if self._output_samplerate is None:
            self._output_samplerate = int(sd.query_devices(kind="output")["default_samplerate"])
        samples = _resample(samples, samplerate, self._output_samplerate)
        samples = _fade_edges(samples, self._output_samplerate)
        sd.play(samples, self._output_samplerate)
        sd.wait()
