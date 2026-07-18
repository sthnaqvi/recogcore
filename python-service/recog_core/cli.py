"""Console-script entry points. `run` is wired up for real in Phase 6."""
from __future__ import annotations

import argparse
from pathlib import Path


def run() -> None:
    print("recogcore run: main recognition loop is built in Phase 6 (not implemented yet).")
    print("For now, use `python scripts/run_face_detection.py` to see live detection+recognition.")


def train() -> None:
    parser = argparse.ArgumentParser(prog="recogcore-train")
    parser.add_argument("--capture", metavar="NAME", help="capture training photos live via the camera")
    parser.add_argument(
        "--import", dest="import_name", metavar="NAME",
        help="import existing photos for NAME instead of live capture (use with --source)",
    )
    parser.add_argument(
        "--source", metavar="PATH",
        help="file or directory of photos to import (jpg/png/heic/etc.) -- used with --import",
    )
    parser.add_argument("--build", action="store_true", help="build embeddings from captured/imported photos")
    args = parser.parse_args()

    if args.import_name:
        if not args.source:
            parser.error("--import requires --source <path>")
        from recog_core.vision.import_photos import import_photos

        import_photos(args.import_name, Path(args.source))
    elif args.capture:
        from recog_core.vision.capture_training_photos import capture

        capture(args.capture)
    elif args.build:
        from recog_core.vision.capture_training_photos import build

        build()
    else:
        parser.print_help()
