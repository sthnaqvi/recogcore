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
    recognition_ambiguity_margin: float
    greeting_known_phrasings: list[str]
    greeting_unknown_phrasings: list[str]
    greeting_cooldown_seconds: float
    greeting_stable_recognitions: int
    tts_length_scale: float
    stt_engine: str
    conversation_mode: str
    conversation_max_turns: int
    conversation_listen_seconds: float


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
    tts = raw.get("tts", {})
    stt = raw.get("stt", {})
    conversation = raw.get("conversation", {})
    return Config(
        hardware_mode=os.environ.get("HARDWARE_MODE", hardware.get("mode", "mac")),
        camera_enabled=hardware.get("camera_enabled", True),
        mic_enabled=hardware.get("mic_enabled", True),
        speaker_enabled=hardware.get("speaker_enabled", True),
        data_dir=REPO_ROOT / "data",
        recognition_threshold=recognition.get("threshold", 0.5),
        recognition_ambiguity_margin=recognition.get("ambiguity_margin", 0.05),
        greeting_known_phrasings=greetings.get("known", DEFAULT_KNOWN_GREETINGS),
        greeting_unknown_phrasings=greetings.get("unknown", DEFAULT_UNKNOWN_GREETINGS),
        greeting_cooldown_seconds=greetings.get("cooldown_seconds", 90),
        greeting_stable_recognitions=greetings.get("stable_recognitions", 3),
        tts_length_scale=tts.get("length_scale", 1.0),
        stt_engine=stt.get("engine", "vosk"),
        conversation_mode=conversation.get("mode", "rules"),
        conversation_max_turns=conversation.get("max_turns", 3),
        conversation_listen_seconds=conversation.get("listen_seconds", 5.0),
    )
