# Phase 4 — STT + two-way conversation

**Est. 20–30 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Turn the one-way greeting (Phase 3) into a real back-and-forth: listen after greeting, transcribe
speech, decide a response, speak it back. The original plan explicitly flags rule-based vs
LLM-API responses as an open cost tradeoff — this phase builds both paths behind a config flag
rather than pre-committing to one.

## Task breakdown

1. Added `vosk` and `faster-whisper` (not `openai-whisper` -- faster-whisper is a drop-in, much
   lighter/faster CTranslate2-based reimplementation, no reason to use the heavier original).
   Benchmarked both against Piper-synthesized test phrases (a clean, automatable stand-in for
   real speech): both transcribed all 3 test phrases correctly; Vosk ~250ms, Whisper-tiny ~180ms.
   Picked **Vosk as the default** anyway -- it never touches the network (Whisper's model
   downloads from Hugging Face Hub on first use), which matters more for a privacy-first home
   device than the small latency difference. Both remain swappable via `config.yaml: stt.engine:
   vosk | whisper`.
2. Write `recog_core/audio/stt.py`: `SpeechToText` interface with `VoskSTT` and `WhisperSTT`
   implementations, both exposing `transcribe(audio: np.ndarray) -> str`, selected via a factory
   analogous to `provider_factory.py` from Phase 0.
3. Write `recog_core/audio/listen.py`: records a bounded window of audio via
   `HardwareProvider.record_audio()` after a greeting (or on wake), with simple silence/VAD-based
   trimming so it doesn't record dead air the whole time (a basic energy-threshold VAD is enough
   to start — no need for a dedicated VAD model yet).
4. Write `recog_core/conversation/intents.py` — the **rule-based path**: a small intent matcher
   (keyword/regex rules) for a fixed set of expected interactions (e.g. "how are you," "what's
   the weather" stubbed/unsupported, "goodbye"), each mapped to a canned response template. This
   is the default, zero-cost path.
5. Write `recog_core/conversation/llm_responder.py` — the **LLM path**: calls an LLM API (e.g.
   Claude via the Anthropic API) with the transcribed text + a short system prompt describing the
   assistant's persona, for open-ended replies the rule-based path can't cover. Gate the API key
   via `.env` (never committed), and make this path opt-in via
   `config.yaml: conversation.mode: rules | llm`.
6. Write `recog_core/conversation/responder.py`: the dispatcher — tries rule-based intents first
   (fast, free, deterministic); if `conversation.mode: llm` and no rule matched, falls through to
   `llm_responder`. This hybrid default keeps cost near zero for common interactions while still
   allowing open-ended chat.
7. Wire the full turn loop in `recog_core/conversation/loop.py`: greet (Phase 3) → listen →
   transcribe → respond → speak (Phase 3's `tts.py`) → optionally listen again for a short
   follow-up window before returning to idle detection.
8. Add a hard conversation timeout/turn-limit per interaction (config-driven) so the assistant
   doesn't get stuck listening indefinitely if no one responds.
9. Tests in `tests/test_intents.py` (rule matching over sample transcripts) and
   `tests/test_responder.py` (dispatcher fallthrough logic with a mocked LLM call — never hit
   the real API in tests).
10. Manual verification: benchmark done in step 1. `scripts/run_conversation_demo.py` added for
    live testing (needs only mic+speaker, not camera, so it also runs fine from a sandboxed host
    app unlike anything touching the camera). Sanity-run confirmed the greeting speaks and the
    loop exits cleanly on silence. **Needs the user** to actually talk to it: run the demo from
    Terminal, confirm a rule-covered question ("how are you") gets a canned response, and (with
    `ANTHROPIC_API_KEY` set in `.env` and `conversation.mode: llm`) confirm an open-ended question
    gets an LLM response.

## File/folder layout created by this phase

```
python-service/
├── scripts/
│   ├── download_stt_model.sh
│   └── run_conversation_demo.py
├── models/
│   └── stt/                      # gitignored -- vosk-model-small-en-us-0.15/
├── tests/
│   ├── test_intents.py
│   ├── test_responder.py
│   ├── test_listen.py
│   └── test_conversation_loop.py
└── recog_core/
    ├── config.py                  # updated: stt.engine, conversation.mode/max_turns/listen_seconds
    ├── audio/
    │   ├── stt.py
    │   └── listen.py
    └── conversation/
        ├── __init__.py
        ├── intents.py
        ├── llm_responder.py
        ├── responder.py
        └── loop.py
```
