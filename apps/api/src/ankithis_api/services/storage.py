import os
import uuid
from pathlib import Path

from ankithis_api.config import settings


def save_upload(content: bytes, filename: str) -> str:
    """Save uploaded file to local storage. Returns the storage path."""
    ext = Path(filename).suffix
    storage_name = f"{uuid.uuid4().hex}{ext}"
    storage_dir = Path(settings.storage_local_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    path = storage_dir / storage_name
    path.write_bytes(content)
    return str(path)


def read_file(storage_path: str) -> bytes:
    """Read a stored file."""
    return Path(storage_path).read_bytes()


def delete_file(storage_path: str) -> None:
    """Delete a stored file if it exists."""
    path = Path(storage_path)
    if path.exists():
        path.unlink()
