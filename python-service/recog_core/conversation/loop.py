from __future__ import annotations

from recog_core.audio.listen import listen
from recog_core.audio.stt import SpeechToText
from recog_core.audio.tts import TextToSpeech
from recog_core.conversation.responder import get_response

DEFAULT_MAX_TURNS = 3
DEFAULT_LISTEN_SECONDS = 5.0
MIN_SPEECH_SAMPLES = 1600  # ~0.1s at 16kHz -- below this, treat as "no response" and end the turn


def run_conversation(
    provider,
    tts: TextToSpeech,
    stt: SpeechToText,
    opening_greeting: str,
    conversation_mode: str = "rules",
    max_turns: int = DEFAULT_MAX_TURNS,
    listen_seconds: float = DEFAULT_LISTEN_SECONDS,
) -> None:
    """Speaks `opening_greeting`, then runs up to `max_turns` listen -> transcribe -> respond ->
    speak turns, stopping early the moment the person doesn't say anything (a hard turn-limit and
    an empty-response cutoff, so the assistant never gets stuck listening indefinitely).

    Blocking by design -- callers run this in its own thread so it doesn't stall the camera loop
    for other people while one conversation is in progress."""
    _speak(provider, tts, opening_greeting)

    for _turn in range(max_turns):
        audio = listen(provider, listen_seconds)
        if len(audio) < MIN_SPEECH_SAMPLES:
            break

        text = stt.transcribe(audio)
        if not text.strip():
            break

        response = get_response(text, mode=conversation_mode)
        _speak(provider, tts, response)


def _speak(provider, tts: TextToSpeech, text: str) -> None:
    samples = tts.synthesize(text)
    provider.play_audio(samples, tts.samplerate)
