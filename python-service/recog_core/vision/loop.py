from __future__ import annotations

import argparse
import time

import cv2

from recog_core.config import load_config
from recog_core.provider_factory import get_provider
from recog_core.vision.face_detector import FaceDetector

WINDOW_NAME = "RecogCore -- Face Detection"
FPS_WINDOW = 30


def run(headless: bool = False) -> None:
    config = load_config()
    provider = get_provider(config)
    detector = FaceDetector()
    provider.start()

    frame_times: list[float] = []
    try:
        while True:
            frame = provider.get_frame()
            if frame is None:
                print("No frame available -- camera disabled or read failed.")
                break

            start = time.time()
            boxes = detector.detect(frame)
            frame_times.append(time.time() - start)
            frame_times = frame_times[-FPS_WINDOW:]
            fps = 1.0 / (sum(frame_times) / len(frame_times)) if frame_times else 0.0

            for box in boxes:
                cv2.rectangle(frame, (box.x, box.y), (box.x + box.w, box.y + box.h), (0, 255, 0), 2)
                cv2.putText(
                    frame, f"{box.confidence:.2f}", (box.x, max(box.y - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
                )
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
    parser = argparse.ArgumentParser(description="Phase 1 face detection loop")
    parser.add_argument("--headless", action="store_true", help="run without a preview window")
    args = parser.parse_args()
    run(headless=args.headless)


if __name__ == "__main__":
    main()
