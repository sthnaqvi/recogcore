from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]


DEFAULT_KNOWN_GREETINGS = ["Hi, {name}!", "Welcome back, {name}!", "Hey {name}, good to see you!"]
DEFAULT_UNKNOWN_GREETINGS = ["Hi there!", "Hello!"]


@dataclass
class Config:
    hardware_mode: str
    camera_enabled: bool
    mic_enabled: bool
    speaker_enabled: bool
    data_dir: Path
    recognition_threshold: float
    greeting_known_phrasings: list[str]
    greeting_unknown_phrasings: list[str]
    greeting_cooldown_seconds: float


def load_config() -> Config:
    load_dotenv(REPO_ROOT / ".env")

    config_path = REPO_ROOT / "config.yaml"
    if not config_path.exists():
        config_path = REPO_ROOT / "config.example.yaml"

    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    hardware = raw.get("hardware", {})
    recognition = raw.get("recognition", {})
    greetings = raw.get("greetings", {})
    return Config(
        hardware_mode=os.environ.get("HARDWARE_MODE", hardware.get("mode", "mac")),
        camera_enabled=hardware.get("camera_enabled", True),
        mic_enabled=hardware.get("mic_enabled", True),
        speaker_enabled=hardware.get("speaker_enabled", True),
        data_dir=REPO_ROOT / "data",
        recognition_threshold=recognition.get("threshold", 0.6),
        greeting_known_phrasings=greetings.get("known", DEFAULT_KNOWN_GREETINGS),
        greeting_unknown_phrasings=greetings.get("unknown", DEFAULT_UNKNOWN_GREETINGS),
        greeting_cooldown_seconds=greetings.get("cooldown_seconds", 90),
    )
