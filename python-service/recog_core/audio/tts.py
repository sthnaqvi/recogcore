from __future__ import annotations

import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

import numpy as np

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "tts" / "en_US-lessac-medium.onnx"
SAMPLE_RATE = 22050


class TextToSpeech:
    """Wraps the Piper CLI via subprocess rather than importing the `piper` package directly --
    Piper is GPL-3.0 licensed, and invoking it as an arm's-length subprocess (like calling
    ffmpeg) keeps that copyleft boundary clean from this MIT-licensed codebase.

    Returns raw float32 PCM samples in [-1, 1] so callers can hand them straight to
    HardwareProvider.play_audio() without knowing anything about Piper."""

    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Piper voice model not found at {model_path}. Run scripts/download_tts_model.sh first."
            )
        self._model_path = model_path

    @property
    def samplerate(self) -> int:
        return SAMPLE_RATE

    def synthesize(self, text: str) -> np.ndarray:
        result = subprocess.run(
            [sys.executable, "-m", "piper", "-m", str(self._model_path), "--output-raw"],
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0


PlayAudioFn = Callable[[np.ndarray, int], None]


class AsyncSpeaker:
    """Runs TTS synthesis + playback on a single background worker thread, so greeting speech
    never blocks the camera/recognition loop and multiple greetings never overlap each other."""

    def __init__(self, tts: TextToSpeech, play_audio: PlayAudioFn) -> None:
        self._tts = tts
        self._play_audio = play_audio
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def speak(self, text: str) -> None:
        self._queue.put(text)

    def _worker(self) -> None:
        while True:
            text = self._queue.get()
            try:
                samples = self._tts.synthesize(text)
                self._play_audio(samples, self._tts.samplerate)
            except Exception as exc:  # noqa: BLE001 -- one bad synthesis must not kill all future greetings
                print(f"Greeting speech failed for {text!r}: {exc}")
