import numpy as np

from recog_core.audio.listen import trim_silence

FRAME_SIZE = 400


def _silence(n_frames: int) -> np.ndarray:
    return np.zeros(n_frames * FRAME_SIZE, dtype=np.float32)


def _voiced(n_frames: int, amplitude: float = 0.5) -> np.ndarray:
    return (amplitude * np.ones(n_frames * FRAME_SIZE)).astype(np.float32)


def test_trim_silence_on_pure_silence_returns_empty():
    audio = _silence(10)
    assert len(trim_silence(audio)) == 0


def test_trim_silence_removes_leading_and_trailing_silence():
    audio = np.concatenate([_silence(5), _voiced(5), _silence(5)])
    trimmed = trim_silence(audio)

    assert len(trimmed) == 5 * FRAME_SIZE
    assert np.all(np.abs(trimmed) > 0.01)


def test_trim_silence_on_empty_input_returns_empty():
    assert len(trim_silence(np.array([], dtype=np.float32))) == 0


def test_trim_silence_keeps_all_voiced_audio_untouched():
    audio = _voiced(8)
    trimmed = trim_silence(audio)
    assert len(trimmed) == len(audio)
