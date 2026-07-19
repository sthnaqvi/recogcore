import numpy as np
import pytest

from recog_core.config import Config
from recog_core.hardware.null_provider import NullProvider
from recog_core.provider_factory import get_provider


def test_null_provider_is_fully_disabled():
    provider = NullProvider()
    provider.start()
    assert provider.get_frame() is None
    assert provider.record_audio(1.0).size == 0
    provider.play_audio(np.zeros(10, dtype=np.float32), 16000)
    provider.stop()


def _config(hardware_mode: str, tmp_path) -> Config:
    return Config(
        hardware_mode=hardware_mode,
        camera_enabled=True,
        mic_enabled=True,
        speaker_enabled=True,
        data_dir=tmp_path,
        recognition_threshold=0.6,
        recognition_ambiguity_margin=0.05,
        greeting_known_phrasings=["Hi, {name}!"],
        greeting_unknown_phrasings=["Hi there!"],
        greeting_cooldown_seconds=90,
        greeting_stable_recognitions=3,
        tts_length_scale=1.0,
        stt_engine="vosk",
        conversation_mode="rules",
        conversation_max_turns=3,
        conversation_listen_seconds=5.0,
    )


def test_factory_returns_mac_provider(tmp_path):
    from recog_core.hardware.mac_provider import MacProvider

    provider = get_provider(_config("mac", tmp_path))
    assert isinstance(provider, MacProvider)


def test_factory_rejects_pi_mode_for_now(tmp_path):
    with pytest.raises(NotImplementedError):
        get_provider(_config("pi", tmp_path))


def test_factory_rejects_unknown_mode(tmp_path):
    with pytest.raises(ValueError):
        get_provider(_config("bogus", tmp_path))


def test_resample_is_identity_when_rates_match():
    from recog_core.hardware.mac_provider import _resample

    samples = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    result = _resample(samples, 22050, 22050)
    np.testing.assert_array_equal(result, samples)


def test_resample_changes_length_proportionally():
    from recog_core.hardware.mac_provider import _resample

    samples = np.zeros(22050, dtype=np.float32)  # 1 second at 22050Hz
    result = _resample(samples, 22050, 48000)
    assert abs(len(result) - 48000) <= 1  # should now be ~1 second at 48000Hz


def test_resample_on_empty_input_returns_empty():
    from recog_core.hardware.mac_provider import _resample

    result = _resample(np.array([], dtype=np.float32), 22050, 48000)
    assert len(result) == 0


def test_resample_clips_filter_ringing_overshoot():
    from recog_core.hardware.mac_provider import _resample

    # A sharp square-wave-like transient is exactly what causes FIR-filter ringing overshoot
    samples = np.concatenate([np.ones(50), -np.ones(50)]).astype(np.float32)
    result = _resample(samples, 22050, 48000)
    assert result.max() <= 1.0
    assert result.min() >= -1.0


def test_fade_edges_ramps_start_and_end_to_zero():
    from recog_core.hardware.mac_provider import _fade_edges

    samples = np.ones(48000, dtype=np.float32)  # 1 second at 48000Hz, full amplitude throughout
    result = _fade_edges(samples, samplerate=48000, fade_ms=8.0)

    assert result[0] == pytest.approx(0.0, abs=1e-6)
    assert result[-1] == pytest.approx(0.0, abs=1e-6)
    # middle of the clip should be untouched (well past the 8ms fade window on either side)
    assert result[len(result) // 2] == pytest.approx(1.0)


def test_fade_edges_handles_very_short_clips_without_crashing():
    from recog_core.hardware.mac_provider import _fade_edges

    samples = np.ones(4, dtype=np.float32)
    result = _fade_edges(samples, samplerate=48000, fade_ms=8.0)
    assert len(result) == 4
