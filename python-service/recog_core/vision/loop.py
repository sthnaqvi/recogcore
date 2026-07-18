from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from recog_core.audio.tts import AsyncSpeaker, TextToSpeech
from recog_core.config import load_config
from recog_core.greeting import GreetingCooldown, build_greeting
from recog_core.provider_factory import get_provider
from recog_core.vision.embeddings import generate_embedding
from recog_core.vision.face_detector import BoundingBox, FaceDetector
from recog_core.vision.recognizer import Recognizer

WINDOW_NAME = "RecogCore -- Face Detection"
FPS_WINDOW = 30
KNOWN_COLOR = (0, 255, 0)
UNKNOWN_COLOR = (0, 165, 255)


def _crop_face(frame: np.ndarray, box: BoundingBox, padding: float = 0.2) -> np.ndarray:
    h, w = frame.shape[:2]
    pad_x = int(box.w * padding)
    pad_y = int(box.h * padding)
    x1, y1 = max(box.x - pad_x, 0), max(box.y - pad_y, 0)
    x2, y2 = min(box.x + box.w + pad_x, w), min(box.y + box.h + pad_y, h)
    return frame[y1:y2, x1:x2]


def _make_speaker(config, provider) -> AsyncSpeaker | None:
    if not provider.is_speaker_enabled():
        return None
    try:
        tts = TextToSpeech()
    except FileNotFoundError as exc:
        print(f"Greeting speech disabled: {exc}")
        return None
    return AsyncSpeaker(tts, provider.play_audio)


def run(headless: bool = False) -> None:
    config = load_config()
    provider = get_provider(config)
    detector = FaceDetector()
    embeddings_path = config.data_dir / "training" / "embeddings" / "known_faces.pkl"
    recognizer = Recognizer(embeddings_path, threshold=config.recognition_threshold)
    cooldown = GreetingCooldown(config.greeting_cooldown_seconds)
    provider.start()
    speaker = _make_speaker(config, provider)

    if not recognizer.has_known_faces():
        print("No trained faces yet -- every face will show as 'Unknown'.")
        print("Run `recogcore train --capture <name>` then `recogcore train --build` to train.")

    frame_times: list[float] = []
    try:
        while True:
            frame = provider.get_frame()
            if frame is None:
                print("No frame available -- camera disabled or read failed.")
                break

            start = time.time()
            boxes = detector.detect(frame)

            for box in boxes:
                crop = _crop_face(frame, box)
                label, color = "Unknown", UNKNOWN_COLOR
                if crop.size > 0:
                    embedding = generate_embedding(crop)
                    if embedding is not None:
                        result = recognizer.identify(embedding)
                        color = KNOWN_COLOR if result.is_known else UNKNOWN_COLOR
                        label = f"{result.name} ({result.confidence:.2f})"

                        if speaker is not None and cooldown.should_greet(result.name):
                            cooldown.mark_greeted(result.name)
                            text = build_greeting(
                                result, config.greeting_known_phrasings, config.greeting_unknown_phrasings
                            )
                            speaker.speak(text)

                cv2.rectangle(frame, (box.x, box.y), (box.x + box.w, box.y + box.h), color, 2)
                cv2.putText(
                    frame, label, (box.x, max(box.y - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1,
                )

            frame_times.append(time.time() - start)
            frame_times = frame_times[-FPS_WINDOW:]
            fps = 1.0 / (sum(frame_times) / len(frame_times)) if frame_times else 0.0
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            if headless:
                print(f"FPS: {fps:.1f}  faces: {len(boxes)}")
            else:
                cv2.imshow(WINDOW_NAME, frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        provider.stop()
        detector.close()
        if not headless:
            cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Face detection + recognition + greeting loop")
    parser.add_argument("--headless", action="store_true", help="run without a preview window")
    args = parser.parse_args()
    run(headless=args.headless)


if __name__ == "__main__":
    main()
