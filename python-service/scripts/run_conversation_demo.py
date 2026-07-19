"""Manual end-to-end test of the Phase 4 conversation loop -- greet, listen, transcribe, respond,
speak, repeat. Doesn't need the camera, just mic + speaker, so it also runs fine from inside a
sandboxed host app (only camera capture is TCC-gated on this Mac, mic/speaker aren't).

Run with the venv active, from python-service/:
    python scripts/run_conversation_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recog_core.audio.stt import get_stt
from recog_core.audio.tts import TextToSpeech
from recog_core.config import load_config
from recog_core.conversation.loop import run_conversation
from recog_core.provider_factory import get_provider


def main() -> None:
    config = load_config()
    config.camera_enabled = False  # this demo is audio-only; never opens the camera
    provider = get_provider(config)
    provider.start()

    print(f"STT engine: {config.stt_engine}  |  conversation mode: {config.conversation_mode}")
    tts = TextToSpeech(length_scale=config.tts_length_scale)
    stt = get_stt(config.stt_engine)

    try:
        run_conversation(
            provider,
            tts,
            stt,
            opening_greeting="Hi there! How are you?",
            conversation_mode=config.conversation_mode,
            max_turns=config.conversation_max_turns,
            listen_seconds=config.conversation_listen_seconds,
        )
    finally:
        provider.stop()


if __name__ == "__main__":
    main()
