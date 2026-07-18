"""Console-script entry points. `run` is wired up for real in Phase 6."""
from __future__ import annotations

import argparse


def run() -> None:
    print("recogcore run: main recognition loop is built in Phase 6 (not implemented yet).")
    print("For now, use `python scripts/run_face_detection.py` to see live detection+recognition.")


def train() -> None:
    parser = argparse.ArgumentParser(prog="recogcore-train")
    parser.add_argument("--capture", metavar="NAME", help="capture training photos for NAME")
    parser.add_argument("--build", action="store_true", help="build embeddings from captured photos")
    args = parser.parse_args()

    if args.capture:
        from recog_core.vision.capture_training_photos import capture

        capture(args.capture)
    elif args.build:
        from recog_core.vision.capture_training_photos import build

        build()
    else:
        parser.print_help()
