import numpy as np

from recog_core.conversation.loop import run_conversation


class FakeProvider:
    def __init__(self, responses: list[np.ndarray]) -> None:
        self._responses = list(responses)
        self.played: list[np.ndarray] = []

    def record_audio(self, seconds: float) -> np.ndarray:
        if self._responses:
            return self._responses.pop(0)
        return np.zeros(10, dtype=np.float32)

    def play_audio(self, samples: np.ndarray, samplerate: int) -> None:
        self.played.append(samples)


class FakeTTS:
    samplerate = 16000

    def synthesize(self, text: str) -> np.ndarray:
        return np.array([len(text)], dtype=np.float32)


class FakeSTT:
    def __init__(self, transcripts: list[str]) -> None:
        self._transcripts = list(transcripts)

    def transcribe(self, audio: np.ndarray) -> str:
        return self._transcripts.pop(0) if self._transcripts else ""


def _voiced_audio(n: int = 2000) -> np.ndarray:
    return (0.5 * np.ones(n)).astype(np.float32)


def test_conversation_always_speaks_the_opening_greeting():
    provider = FakeProvider(responses=[np.zeros(10, dtype=np.float32)])
    run_conversation(provider, FakeTTS(), FakeSTT(transcripts=[]), "Hi there!", max_turns=3)
    assert len(provider.played) == 1


def test_conversation_ends_immediately_when_no_speech_detected():
    provider = FakeProvider(responses=[np.zeros(10, dtype=np.float32)])
    stt = FakeSTT(transcripts=["should not be reached"])
    run_conversation(provider, FakeTTS(), stt, "Hi!", max_turns=3)
    assert len(provider.played) == 1


def test_conversation_runs_one_turn_then_stops_on_silence():
    provider = FakeProvider(responses=[_voiced_audio(), np.zeros(10, dtype=np.float32)])
    stt = FakeSTT(transcripts=["how are you"])
    run_conversation(provider, FakeTTS(), stt, "Hi!", max_turns=3)
    # greeting + one response = 2 playbacks; turn 2 gets silence and stops
    assert len(provider.played) == 2


def test_conversation_stops_at_max_turns_even_if_still_talking():
    provider = FakeProvider(responses=[_voiced_audio() for _ in range(5)])
    stt = FakeSTT(transcripts=["how are you", "thanks", "goodbye", "more", "more"])
    run_conversation(provider, FakeTTS(), stt, "Hi!", max_turns=2)
    # greeting + 2 turns (hard cap) = 3 playbacks
    assert len(provider.played) == 3
