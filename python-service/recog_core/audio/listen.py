from __future__ import annotations

import numpy as np

DEFAULT_LISTEN_SECONDS = 5.0
DEFAULT_SILENCE_THRESHOLD = 0.02  # RMS amplitude below this is treated as silence
FRAME_SIZE = 400  # 25ms at 16kHz


def trim_silence(
    audio: np.ndarray, threshold: float = DEFAULT_SILENCE_THRESHOLD, frame_size: int = FRAME_SIZE
) -> np.ndarray:
    """Trims leading/trailing silence using simple energy-threshold VAD (RMS per frame) -- no
    dedicated VAD model needed at this scale, per the phase-4 plan."""
    if len(audio) == 0:
        return audio

    n_frames = max(len(audio) // frame_size, 1)
    frame_rms = np.array(
        [np.sqrt(np.mean(audio[i * frame_size : (i + 1) * frame_size] ** 2)) for i in range(n_frames)]
    )
    voiced = np.where(frame_rms > threshold)[0]
    if len(voiced) == 0:
        return np.array([], dtype=audio.dtype)

    start = voiced[0] * frame_size
    end = min((voiced[-1] + 1) * frame_size, len(audio))
    return audio[start:end]


def listen(provider, seconds: float = DEFAULT_LISTEN_SECONDS) -> np.ndarray:
    """Records `seconds` of audio via the HardwareProvider, then trims leading/trailing silence
    so the STT engine isn't fed a window that's mostly dead air."""
    audio = provider.record_audio(seconds)
    return trim_silence(audio)
