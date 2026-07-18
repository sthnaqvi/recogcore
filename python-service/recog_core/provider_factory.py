from __future__ import annotations

from .config import Config
from .hardware.base import HardwareProvider
from .hardware.mac_provider import MacProvider


def get_provider(config: Config) -> HardwareProvider:
    if config.hardware_mode == "mac":
        return MacProvider(
            camera_enabled=config.camera_enabled,
            mic_enabled=config.mic_enabled,
            speaker_enabled=config.speaker_enabled,
        )
    if config.hardware_mode == "pi":
        raise NotImplementedError("PiProvider is implemented in Phase 8")
    raise ValueError(f"Unknown HARDWARE_MODE: {config.hardware_mode!r}")
