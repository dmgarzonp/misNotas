"""Unit tests for ImageManager service."""

import os
import tempfile
from src.services.image_manager import ImageManager


def test_import_image_success():
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = ImageManager(storage_dir=os.path.join(tmp_dir, "assets"))

        # Create dummy image file
        src_file = os.path.join(tmp_dir, "test.png")
        with open(src_file, "wb") as f:
            f.write(b"PNG_DUMMY_DATA")

        file_url = manager.import_image(src_file)
        assert file_url is not None
        assert file_url.startswith("file://")
        assert os.path.exists(file_url.replace("file://", ""))


def test_import_image_invalid_extension():
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = ImageManager(storage_dir=os.path.join(tmp_dir, "assets"))

        src_file = os.path.join(tmp_dir, "test.txt")
        with open(src_file, "w") as f:
            f.write("text data")

        file_url = manager.import_image(src_file)
        assert file_url is None
