"""Unit tests for SingleInstanceGuard service."""

import pytest
from PyQt6.QtCore import QCoreApplication
from src.services.single_instance import SingleInstanceGuard


@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


def test_single_instance_guard_lifecycle():
    socket_name = "test_mis_apuntes_single_instance_test_socket"

    guard_primary = SingleInstanceGuard(socket_name=socket_name)
    assert not guard_primary.is_another_instance_running()

    activated = False

    def on_activate():
        nonlocal activated
        activated = True

    assert guard_primary.start_server(on_activate)

    # Secondary instance test
    guard_secondary = SingleInstanceGuard(socket_name=socket_name)
    assert guard_secondary.is_another_instance_running()

    # Process events to allow server to handle connection
    QCoreApplication.processEvents()
    assert activated
