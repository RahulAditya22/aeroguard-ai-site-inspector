from PIL import Image
import pytest

from aeroguard.image_utils import validate_image


def test_valid_jpeg(tmp_path):
    path = tmp_path / "site.jpg"
    Image.new("RGB", (100, 80), "white").save(path, format="JPEG")
    info = validate_image(path)
    assert info.mime_type == "image/jpeg"
    assert info.width == 100
    assert info.height == 80


def test_missing_image():
    with pytest.raises(FileNotFoundError):
        validate_image("missing.jpg")


def test_unsupported_extension(tmp_path):
    path = tmp_path / "site.txt"
    path.write_text("not an image", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported image type"):
        validate_image(path)
