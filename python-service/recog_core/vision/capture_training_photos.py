from __future__ import annotations

import time

import cv2

from recog_core.config import load_config
from recog_core.provider_factory import get_provider
from recog_core.vision.embeddings import build_known_faces_db, save_known_faces_db

TARGET_SHOT_COUNT = 18
WINDOW_NAME = "RecogCore -- Capture Training Photos"


def capture(name: str) -> None:
    """Interactive capture flow: SPACE to save a shot, 'q' to stop early. Saves to
    data/training/faces/<name>/ (gitignored -- never committed)."""
    config = load_config()
    provider = get_provider(config)
    provider.start()

    out_dir = config.data_dir / "training" / "faces" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Capturing training photos for '{name}'.")
    print(f"Vary your angle and lighting between shots. Target: {TARGET_SHOT_COUNT} photos.")
    print("SPACE = capture a shot, q = stop early.")

    shot_count = 0
    try:
        while shot_count < TARGET_SHOT_COUNT:
            frame = provider.get_frame()
            if frame is None:
                print("No camera frame available.")
                break

            preview = frame.copy()
            cv2.putText(
                preview, f"Shots: {shot_count}/{TARGET_SHOT_COUNT}  (SPACE=capture, q=quit)",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
            )
            cv2.imshow(WINDOW_NAME, preview)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(" "):
                shot_path = out_dir / f"{name}_{shot_count:02d}_{int(time.time())}.jpg"
                cv2.imwrite(str(shot_path), frame)
                shot_count += 1
                print(f"Saved {shot_path.name} ({shot_count}/{TARGET_SHOT_COUNT})")
            elif key == ord("q"):
                break
    finally:
        provider.stop()
        cv2.destroyAllWindows()

    print(f"Done -- {shot_count} photo(s) saved to {out_dir}")


def build() -> None:
    """Walks data/training/faces/*/ and (re)builds data/training/embeddings/known_faces.pkl."""
    config = load_config()
    training_dir = config.data_dir / "training"
    known = build_known_faces_db(training_dir)

    if not known:
        print(f"No training photos found under {training_dir / 'faces'}/<name>/ -- nothing to build.")
        print("Run `recogcore train --capture <name>` first.")
        return

    embeddings_path = training_dir / "embeddings" / "known_faces.pkl"
    save_known_faces_db(known, embeddings_path)
    for person_name, encodings in known.items():
        print(f"{person_name}: {len(encodings)} encoding(s)")
    print(f"Saved {embeddings_path}")
