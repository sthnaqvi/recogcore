import numpy as np
import pytest
from PIL import Image

from recog_core.vision.import_photos import (
    MAX_DIMENSION,
    _find_image_files,
    _load_and_normalize,
    import_photos,
)


def _save_noise_image(path, size=(200, 200)) -> None:
    array = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    Image.fromarray(array).save(path)


def test_find_image_files_filters_by_extension(tmp_path):
    _save_noise_image(tmp_path / "a.jpg")
    _save_noise_image(tmp_path / "b.png")
    (tmp_path / "notes.txt").write_text("not an image")

    found = _find_image_files(tmp_path)
    assert {p.name for p in found} == {"a.jpg", "b.png"}


def test_find_image_files_accepts_single_file(tmp_path):
    photo = tmp_path / "a.jpg"
    _save_noise_image(photo)
    assert _find_image_files(photo) == [photo]


def test_load_and_normalize_downscales_oversized_images(tmp_path):
    photo = tmp_path / "big.jpg"
    _save_noise_image(photo, size=(3000, 2000))

    normalized = _load_and_normalize(photo)
    assert max(normalized.size) <= MAX_DIMENSION


def test_load_and_normalize_leaves_small_images_untouched(tmp_path):
    photo = tmp_path / "small.jpg"
    _save_noise_image(photo, size=(200, 150))

    normalized = _load_and_normalize(photo)
    assert normalized.size == (200, 150)


def test_import_photos_raises_on_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        import_photos("alice", tmp_path / "does-not-exist", data_dir=tmp_path)


def test_import_photos_returns_zero_when_no_supported_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.txt").write_text("no images here")

    count = import_photos("alice", source, data_dir=tmp_path / "data")
    assert count == 0


def test_import_photos_skips_images_with_no_detectable_face(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _save_noise_image(source / "photo1.jpg")
    _save_noise_image(source / "photo2.png")

    data_dir = tmp_path / "data"
    count = import_photos("alice", source, data_dir=data_dir)

    assert count == 0
    out_dir = data_dir / "training" / "faces" / "alice"
    assert not out_dir.exists() or list(out_dir.iterdir()) == []
