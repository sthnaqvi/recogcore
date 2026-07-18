"""Manual entry point for Phase 1 face detection.

Run with the venv active, from python-service/, in a plain Terminal window (not a sandboxed
host app) so macOS can grant camera access:
    python scripts/run_face_detection.py [--headless]

Equivalently: python -m recog_core.vision.loop [--headless]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recog_core.vision.loop import main

if __name__ == "__main__":
    main()
