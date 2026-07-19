# How RecogCore works

A high-level explainer of what each capability does, which library/model powers it, and which
method actually gets called — meant for browsing on GitHub or explaining the project to someone
else, not for reading source code. It does **not** explain how the underlying ML models work
internally (no neural-net internals) — just how *this project* uses them.

For the build roadmap see [PLAN.md](PLAN.md); for detailed task-by-task plans see
[plan/](plan/); for known bugs/improvements see [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## At a glance

| Capability | Library | Model | Key method |
|---|---|---|---|
| Camera / mic / speaker | OpenCV, `sounddevice` | — | `get_frame()`, `record_audio()`, `play_audio()` |
| Face detection | MediaPipe (Tasks API) | `blaze_face_short_range` (~230KB) | `FaceDetector.detect()` |
| Face recognition | `face_recognition` (built on `dlib`) | dlib's bundled face-recognition network | `face_encodings()`, `face_distance()` |
| Text-to-speech | Piper (via subprocess) | `en_US-lessac-medium` (~63MB) | `TextToSpeech.synthesize()` |
| Speech-to-text | Vosk (default) or `faster-whisper` | `vosk-model-small-en-us-0.15` (~41MB) / Whisper `tiny` | `transcribe()` |
| Conversation | hand-written keyword rules + Claude (optional) | `claude-haiku-4-5` | `match_intent()`, `get_llm_response()` |

## The pipeline

```
camera frame → detect faces → crop each face → recognize → greet (speak) → listen → transcribe → respond → speak
```

## 1. Hardware abstraction

**What:** one interface, `HardwareProvider`, for camera/mic/speaker — so the exact same
recognition/greeting/conversation code runs unchanged on a Mac (development) and a Raspberry Pi
(deployment, later).

**How:** `MacProvider` implements three methods — `get_frame()` (OpenCV `cv2.VideoCapture`),
`record_audio()` and `play_audio()` (`sounddevice`, which wraps PortAudio) — and every other part
of the codebase calls only those three methods, never `cv2`/`sounddevice` directly. Swapping to a
Pi later means writing one new `PiProvider` class with the same three methods; nothing else in
the project changes.

## 2. Face detection

**What:** find *where* faces are in a frame (a box per face + a confidence score) — not who they
are.

**How:** each frame is converted to RGB and passed to **MediaPipe**'s `FaceDetector.detect()`,
which runs the `blaze_face_short_range` model (chosen because it's tuned for faces within ~2
meters, matching a stationary entryway camera) and returns a list of bounding boxes. This step
has no concept of identity — it just says "there's a face at (x, y)."

## 3. Face recognition

**What:** given a detected face, decide whether it's someone trained (and who) or a stranger.

**How:**
1. Crop the face out of the frame using the box from step 2 (with a little padding).
2. Run `face_recognition.face_encodings()` on the crop, producing a **128-number vector** (an
   "embedding") that captures what that specific face looks like. Two photos of the same person
   produce very similar vectors; two different people produce very different ones.
3. During training (`recogcore-train --capture`/`--import`/`--build`), this same encoding step
   runs on every training photo of every person, and the results are saved to
   `data/training/embeddings/known_faces.pkl`.
4. At recognition time, `Recognizer.identify()` measures the **Euclidean distance**
   (`face_recognition.face_distance()`) between the live embedding and every saved one, and picks
   the closest match.
5. If that closest distance is at or below `recognition.threshold` (config-driven, default 0.6),
   it's a match — otherwise, "Unknown."

That's the entire trick: encode two faces into two vectors, measure how far apart the vectors
are, and threshold the distance. Nothing in this project trains or fine-tunes a model — `dlib`'s
pretrained encoder does all the "understanding," and RecogCore just compares its outputs.

## 4. Spoken greetings

**What:** speak a name-based or generic greeting out loud.

**How:** `build_greeting()` picks a phrasing template from `config.yaml` (filling in `{name}` for
known people), and hands the resulting sentence to **Piper** — a neural TTS engine, invoked as a
subprocess rather than imported as a library, since Piper is GPL-licensed and this project is
MIT. `TextToSpeech.synthesize()` returns raw audio samples, played back through the same
`HardwareProvider.play_audio()` from step 1. A background thread (`AsyncSpeaker`) does the
synthesis + playback so it never blocks the camera loop, and a per-person cooldown
(`GreetingCooldown`) stops the same person from being re-greeted every single frame while they're
still in view.

## 5. Two-way conversation

**What:** after greeting, listen for a reply, understand it, and respond.

**How:**
1. Record a few seconds of audio, then trim the silence at the start/end.
2. Transcribe it to text — via **Vosk** (fully offline, the default) or **`faster-whisper`**
   (better accuracy, downloads its model from Hugging Face on first use), swappable via
   `config.yaml: stt.engine`.
3. Check the text against a small hand-written set of keyword rules (`match_intent()`) — "how
   are you," "goodbye," "thank you," etc. — each mapped to a canned reply. Free, instant,
   deterministic.
4. If nothing matches *and* `config.yaml: conversation.mode: llm` is set, fall through to
   **Claude** (`claude-haiku-4-5`) for an open-ended reply instead.
5. Speak the response, and repeat from step 1 — up to a fixed number of turns, or until the
   person stops responding.

## Where things are heading

Entry/exit logging to MySQL, an optional web dashboard, and a Raspberry Pi deployment (behind the
same `HardwareProvider` interface, so none of the above changes) are next — see the full
phase-by-phase roadmap in [PLAN.md](PLAN.md).
