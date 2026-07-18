from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Config:
    hardware_mode: str
    camera_enabled: bool
    mic_enabled: bool
    speaker_enabled: bool
    data_dir: Path
    recognition_threshold: float


def load_config() -> Config:
    load_dotenv(REPO_ROOT / ".env")

    config_path = REPO_ROOT / "config.yaml"
    if not config_path.exists():
        config_path = REPO_ROOT / "config.example.yaml"

    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    hardware = raw.get("hardware", {})
    recognition = raw.get("recognition", {})
    return Config(
        hardware_mode=os.environ.get("HARDWARE_MODE", hardware.get("mode", "mac")),
        camera_enabled=hardware.get("camera_enabled", True),
        mic_enabled=hardware.get("mic_enabled", True),
        speaker_enabled=hardware.get("speaker_enabled", True),
        data_dir=REPO_ROOT / "data",
        recognition_threshold=recognition.get("threshold", 0.6),
    )
