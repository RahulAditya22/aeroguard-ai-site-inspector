"""Image validation and metadata helpers."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class ImageInfo:
    path: Path
    mime_type: str
    width: int
    height: int
    size_bytes: int


def validate_image(path: str | Path, max_image_mb: int = 15) -> ImageInfo:
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image type '{image_path.suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    size_bytes = image_path.stat().st_size
    if size_bytes > max_image_mb * 1024 * 1024:
        raise ValueError(f"Image exceeds the {max_image_mb} MB limit: {image_path}")

    try:
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            width, height = image.size
            format_name = (image.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Invalid or unreadable image: {image_path}") from exc

    mime_by_format = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    mime_type = mime_by_format.get(format_name)
    if mime_type is None:
        raise ValueError(f"Unsupported image format: {format_name or 'unknown'}")

    return ImageInfo(
        path=image_path,
        mime_type=mime_type,
        width=width,
        height=height,
        size_bytes=size_bytes,
    )
