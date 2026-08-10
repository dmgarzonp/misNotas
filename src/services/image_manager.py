"""Image Manager service for Mis Apuntes application.

Handles local copying, storage, and file URL formatting for images
inserted into notes to prevent broken image links using QStandardPaths.
"""

import os
import shutil
import uuid
from typing import Optional
from PyQt6.QtCore import QStandardPaths
from src.interfaces.services import IImageManager


def get_default_image_storage_dir() -> str:
    """Resolves standard Linux AppData location for image assets (~/.local/share/misNotas/images)."""
    base_dir = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    if not base_dir:
        base_dir = os.path.expanduser("~/.local/share/misNotas")
    img_dir = os.path.join(base_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    return img_dir


class ImageManager(IImageManager):
    """Manages local storage of note image attachments using QStandardPaths."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        if storage_dir is None:
            self.storage_dir = get_default_image_storage_dir()
        else:
            self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)

    def import_image(self, original_path: str) -> Optional[str]:
        """Copies an image from original_path into local storage_dir and returns file:// URL."""
        if not os.path.exists(original_path):
            return None

        ext = os.path.splitext(original_path)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"):
            return None

        unique_name = f"{uuid.uuid4().hex[:10]}{ext}"
        dest_path = os.path.join(self.storage_dir, unique_name)
        shutil.copy2(original_path, dest_path)

        return f"file://{dest_path}"
