"""Image loading, validation, and metadata extraction using Pillow/NumPy."""

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image

ALLOWED_FORMATS = {"PNG", "JPEG", "JPG", "TIFF"}
ALLOWED_MIME_TYPES = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/tiff": "TIFF",
}


class InvalidImageError(Exception):
    pass


@dataclass
class ImageMeta:
    width: int
    height: int
    format: str
    mode: str
    size_bytes: int


def validate_and_load(file_bytes: bytes, content_type: str | None) -> tuple[Image.Image, ImageMeta]:
    """Validate an uploaded image and return (PIL Image, metadata).

    Raises InvalidImageError with a user-friendly message on failure.
    """
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise InvalidImageError(
            f"Unsupported image format '{content_type}'. Supported: PNG, JPG, JPEG, TIFF."
        )

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.load()
    except Exception as e:
        raise InvalidImageError("This file could not be read as an image.") from e

    if img.format not in ALLOWED_FORMATS:
        raise InvalidImageError(
            f"Unsupported image format '{img.format}'. Supported: PNG, JPG, JPEG, TIFF."
        )

    meta = ImageMeta(
        width=img.width,
        height=img.height,
        format=img.format,
        mode=img.mode,
        size_bytes=len(file_bytes),
    )
    return img, meta


def to_rgb_array(img: Image.Image) -> np.ndarray:
    """Convert a PIL image to an RGB numpy array."""
    return np.array(img.convert("RGB"))


def resize_for_model(img: Image.Image, max_dim: int = 1024) -> Image.Image:
    """Downscale an image so its largest dimension is at most max_dim,
    preserving aspect ratio. Used before sending to Gemini or CV models
    to keep payloads reasonable."""
    w, h = img.size
    if max(w, h) <= max_dim:
        return img
    scale = max_dim / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def image_to_bytes(img: Image.Image, format: str = "JPEG") -> bytes:
    buf = io.BytesIO()
    if format == "JPEG" and img.mode != "RGB":
        img = img.convert("RGB")
    save_kwargs = {"quality": 90} if format == "JPEG" else {}
    img.save(buf, format=format, **save_kwargs)
    return buf.getvalue()
