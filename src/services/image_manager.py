"""Image Manager service for Mis Apuntes application.

Handles local copying, storage, and file URL formatting for images
inserted into notes to prevent broken image links.
"""

import os
import shutil
import uuid
from typing import Optional


class ImageManager:
    """Manages local storage of note image attachments in data/images directory."""

    def __init__(self, storage_dir: str = "data/images") -> None:
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
