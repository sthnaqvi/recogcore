from __future__ import annotations

from pathlib import Path

import face_recognition
import numpy as np
from PIL import Image, ImageOps

from recog_core.config import load_config

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()  # lets PIL.Image.open() read .heic/.heif transparently
except ImportError:
    pass

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".bmp", ".tiff", ".webp"}
MAX_DIMENSION = 1600  # longest side, in pixels -- plenty for face embeddings, keeps files small
JPEG_QUALITY = 90

try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:  # older Pillow
    _RESAMPLE = Image.LANCZOS


def _find_image_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source] if source.suffix.lower() in SUPPORTED_EXTENSIONS else []
    return sorted(
        p for p in source.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def _load_and_normalize(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image = ImageOps.exif_transpose(image)  # phone photos (esp. HEIC) often carry rotation in EXIF
    if max(image.size) > MAX_DIMENSION:
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), _RESAMPLE)
    return image


def import_photos(name: str, source: Path, data_dir: Path | None = None) -> int:
    """Import existing photos for `name` instead of live capture -- handles large phone photos
    (downscaled to MAX_DIMENSION) and Apple's HEIC/HEIF format (converted to JPEG). Skips any
    image with no detectable face. Saves into data/training/faces/<name>/ like live capture does.
    Returns the number of photos imported.

    `data_dir` defaults to the configured repo data dir; tests pass a tmp_path override so they
    never write into the real, gitignored data/ tree."""
    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    image_paths = _find_image_files(source)
    if not image_paths:
        print(f"No supported images found under {source} (looked for {sorted(SUPPORTED_EXTENSIONS)})")
        return 0

    if data_dir is None:
        data_dir = load_config().data_dir
    out_dir = data_dir / "training" / "faces" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    imported = 0
    for i, path in enumerate(image_paths):
        try:
            image = _load_and_normalize(path)
        except Exception as exc:
            print(f"Skipping {path.name}: could not read image ({exc})")
            continue

        if not face_recognition.face_locations(np.array(image)):
            print(f"Skipping {path.name}: no face detected")
            continue

        out_path = out_dir / f"{name}_{i:03d}_{path.stem}.jpg"
        image.save(out_path, "JPEG", quality=JPEG_QUALITY)
        imported += 1
        print(f"Imported {path.name} -> {out_path.name}")

    print(f"Done -- {imported}/{len(image_paths)} photo(s) imported to {out_dir}")
    return imported
