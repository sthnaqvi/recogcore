from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from recog_core.audio.tts import AsyncSpeaker, TextToSpeech
from recog_core.config import load_config
from recog_core.greeting import GreetingCooldown, GreetingStabilizer, build_greeting
from recog_core.provider_factory import get_provider
from recog_core.vision.embeddings import generate_embedding
from recog_core.vision.face_detector import BoundingBox, FaceDetector
from recog_core.vision.recognizer import Recognizer

WINDOW_NAME = "RecogCore -- Face Detection"
FPS_WINDOW = 30
KNOWN_COLOR = (0, 255, 0)
UNKNOWN_COLOR = (0, 165, 255)
RECOGNITION_EVERY_N_FRAMES = 5  # face encoding is the expensive step; detection+drawing still run every frame

Label = tuple[str, tuple[int, int, int]]
CachedLabel = tuple[float, float, Label]  # (center_x, center_y, label) from the last recognition pass


def _crop_face(
    frame: np.ndarray, box: BoundingBox, padding: float = 0.2
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Returns the padded crop plus the tight face box within it as (top, right, bottom, left),
    so the embedding step can align on the actual face rather than the padded crop."""
    h, w = frame.shape[:2]
    pad_x = int(box.w * padding)
    pad_y = int(box.h * padding)
    x1, y1 = max(box.x - pad_x, 0), max(box.y - pad_y, 0)
    x2, y2 = min(box.x + box.w + pad_x, w), min(box.y + box.h + pad_y, h)
    crop = frame[y1:y2, x1:x2]

    top = max(box.y - y1, 0)
    left = max(box.x - x1, 0)
    bottom = min(top + box.h, y2 - y1)
    right = min(left + box.w, x2 - x1)
    return crop, (top, right, bottom, left)


def _nearest_cached_label(box: BoundingBox, cached: list[CachedLabel]) -> Label:
    """Match a box to the closest cached label by center position, NOT by list index -- the
    detector's box ordering can change between frames, and index-matching once put one person's
    cached name on another person's face for the frames between recognition passes."""
    cx, cy = box.x + box.w / 2, box.y + box.h / 2
    best: Label | None = None
    best_sq = float("inf")
    for px, py, label in cached:
        sq = (px - cx) ** 2 + (py - cy) ** 2
        if sq < best_sq:
            best_sq, best = sq, label
    if best is not None and best_sq <= float(box.w) ** 2:
        return best
    return ("...", UNKNOWN_COLOR)


def _make_speaker(config, provider) -> AsyncSpeaker | None:
    if not provider.is_speaker_enabled():
        return None
    try:
        tts = TextToSpeech(length_scale=config.tts_length_scale)
    except FileNotFoundError as exc:
        print(f"Greeting speech disabled: {exc}")
        return None
    return AsyncSpeaker(tts, provider.play_audio)


def run(headless: bool = False) -> None:
    config = load_config()
    provider = get_provider(config)
    detector = FaceDetector()
    embeddings_path = config.data_dir / "training" / "embeddings" / "known_faces.pkl"
    recognizer = Recognizer(
        embeddings_path,
        threshold=config.recognition_threshold,
        margin=config.recognition_ambiguity_margin,
    )
    cooldown = GreetingCooldown(config.greeting_cooldown_seconds)
    stabilizer = GreetingStabilizer(config.greeting_stable_recognitions)
    provider.start()
    speaker = _make_speaker(config, provider)

    if not recognizer.has_known_faces():
        print("No trained faces yet -- every face will show as 'Unknown'.")
        print("Run `recogcore train --capture <name>` then `recogcore train --build` to train.")

    frame_times: list[float] = []
    frame_index = 0
    cached_labels: list[CachedLabel] = []
    try:
        while True:
            frame = provider.get_frame()
            if frame is None:
                print("No frame available -- camera disabled or read failed.")
                break

            start = time.time()
            boxes = detector.detect(frame)
            run_recognition = frame_index % RECOGNITION_EVERY_N_FRAMES == 0

            if run_recognition:
                embeddings: list[np.ndarray] = []
                valid_indices: list[int] = []
                for i, box in enumerate(boxes):
                    crop, face_location = _crop_face(frame, box)
                    if crop.size == 0:
                        continue
                    embedding = generate_embedding(crop, face_location)
                    if embedding is not None:
                        embeddings.append(embedding)
                        valid_indices.append(i)

                # Batch identification enforces one-person-one-face per frame (no two boxes
                # can both be the same trained person at once).
                results = recognizer.identify_all(embeddings)

                labels: list[Label] = [("Unknown", UNKNOWN_COLOR)] * len(boxes)
                result_by_name = {}
                for i, result in zip(valid_indices, results):
                    color = KNOWN_COLOR if result.is_known else UNKNOWN_COLOR
                    labels[i] = (f"{result.name} ({result.confidence:.2f})", color)
                    result_by_name.setdefault(result.name, result)

                # Greet only identities that have been stable across consecutive recognition
                # passes -- a one-pass flicker to the wrong name never fires a greeting.
                stable_names = stabilizer.observe(result_by_name.keys())
                for name in stable_names:
                    if speaker is not None and cooldown.should_greet(name):
                        cooldown.mark_greeted(name)
                        text = build_greeting(
                            result_by_name[name],
                            config.greeting_known_phrasings,
                            config.greeting_unknown_phrasings,
                        )
                        speaker.speak(text)

                cached_labels = [
                    (box.x + box.w / 2, box.y + box.h / 2, labels[i])
                    for i, box in enumerate(boxes)
                ]
            else:
                labels = [_nearest_cached_label(box, cached_labels) for box in boxes]

            for i, box in enumerate(boxes):
                text, color = labels[i]
                cv2.rectangle(frame, (box.x, box.y), (box.x + box.w, box.y + box.h), color, 2)
                cv2.putText(
                    frame, text, (box.x, max(box.y - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1,
                )

            frame_index += 1
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
