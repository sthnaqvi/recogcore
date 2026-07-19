from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

DEFAULT_VOSK_MODEL_PATH = (
    Path(__file__).resolve().parents[2] / "models" / "stt" / "vosk-model-small-en-us-0.15"
)
STT_SAMPLE_RATE = 16000  # matches HardwareProvider.record_audio()


class SpeechToText(ABC):
    @abstractmethod
    def transcribe(self, audio: np.ndarray) -> str:
        """`audio` is mono float32 PCM at STT_SAMPLE_RATE (16kHz) -- the same format
        HardwareProvider.record_audio() returns, so no resampling is needed in production."""


class VoskSTT(SpeechToText):
    """Fully offline, no network access ever needed after the model is downloaded once."""

    def __init__(self, model_path: Path = DEFAULT_VOSK_MODEL_PATH) -> None:
        import vosk

        if not model_path.exists():
            raise FileNotFoundError(
                f"Vosk model not found at {model_path}. Run scripts/download_stt_model.sh first."
            )
        vosk.SetLogLevel(-1)
        self._vosk = vosk
        self._model = vosk.Model(str(model_path))

    def transcribe(self, audio: np.ndarray) -> str:
        recognizer = self._vosk.KaldiRecognizer(self._model, STT_SAMPLE_RATE)
        pcm16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
        recognizer.AcceptWaveform(pcm16)
        result = json.loads(recognizer.FinalResult())
        return result.get("text", "")


class WhisperSTT(SpeechToText):
    """Higher accuracy, heavier -- and the chosen model is fetched from Hugging Face Hub on
    first use (cached locally after that), unlike Vosk which never touches the network."""

    def __init__(self, model_size: str = "tiny") -> None:
        from faster_whisper import WhisperModel

        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _info = self._model.transcribe(audio, language="en")
        return " ".join(segment.text.strip() for segment in segments).strip()


def get_stt(engine: str) -> SpeechToText:
    if engine == "vosk":
        return VoskSTT()
    if engine == "whisper":
        return WhisperSTT()
    raise ValueError(f"Unknown STT engine: {engine!r}")
