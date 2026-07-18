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
        greeting_known_phrasings=["Hi, {name}!"],
        greeting_unknown_phrasings=["Hi there!"],
        greeting_cooldown_seconds=90,
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
