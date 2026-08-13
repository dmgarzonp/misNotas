"""Unit tests for AutostartService and UpdateService."""

import os
import tempfile
from src.services.autostart_service import AutostartService
from src.services.update_service import UpdateWorker


def test_autostart_service_enable_and_disable():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = AutostartService(autostart_dir=tmp_dir, systemd_user_dir=tmp_dir)
        assert not service.is_autostart_enabled()

        success_enable = service.enable_autostart()
        assert success_enable
        assert service.is_autostart_enabled()
        assert os.path.exists(service.desktop_file_path)

        # Check content
        with open(service.desktop_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "[Desktop Entry]" in content
            assert "Exec=" in content

        success_disable = service.disable_autostart()
        assert success_disable
        assert not service.is_autostart_enabled()


def test_update_worker_semantic_version_comparison():
    assert UpdateWorker._is_newer_version("1.1.0", "1.0.0")
    assert UpdateWorker._is_newer_version("2.0.0", "1.9.9")
    assert UpdateWorker._is_newer_version("1.0.1", "1.0.0")
    assert not UpdateWorker._is_newer_version("1.0.0", "1.0.0")
    assert not UpdateWorker._is_newer_version("0.9.0", "1.0.0")
