"""Safe file handling helpers for uploaded images."""

import os
import re
import uuid

from app.config import get_settings

settings = get_settings()

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def safe_filename(original_name: str) -> str:
    """Produce a collision-resistant, path-safe filename."""
    base = os.path.basename(original_name or "upload")
    base = _SAFE_CHARS.sub("_", base)
    unique = uuid.uuid4().hex[:10]
    name, ext = os.path.splitext(base)
    return f"{unique}_{name}{ext.lower()}"


def save_upload(file_bytes: bytes, original_name: str) -> str:
    """Persist an uploaded file to the upload directory, returns the path."""
    os.makedirs(settings.upload_dir, exist_ok=True)
    filename = safe_filename(original_name)
    path = os.path.join(settings.upload_dir, filename)
    with open(path, "wb") as f:
        f.write(file_bytes)
    return path


def enforce_size_limit(file_bytes: bytes):
    from fastapi import HTTPException

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds the maximum allowed size of {settings.max_upload_mb}MB.",
        )
