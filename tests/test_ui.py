"""UI integration tests for NoteWindow view, Sidebar, and NoteController."""

import os
import tempfile
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
import pytest

from src.controllers.note_controller import NoteController
from src.models.note_model import NoteRepository
from src.services.auth_service import AuthService
from src.views.note_window import NoteWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_repo():
    NoteController._active_controllers.clear()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    repo = NoteRepository(db_path)
    yield repo
    NoteController._active_controllers.clear()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_note_window_components(qapp):
    window = NoteWindow()
    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert window.sidebar is not None
    assert window.title_input is not None
    assert window.content_edit is not None
    assert window.size_grip is not None


def test_spawn_new_note_window(qapp, temp_repo, qtbot):
    window = NoteWindow()
    qtbot.addWidget(window)
    controller = NoteController(view=window, repository=temp_repo)

    initial_count = len(NoteController._active_controllers)
    new_controller = controller.spawn_new_note_window()
    qtbot.addWidget(new_controller.view)

    assert len(NoteController._active_controllers) == initial_count + 1
    assert new_controller.view != window
    assert new_controller.view.pos().x() > window.pos().x()

    new_controller.close_window()


def test_delete_note_by_id(qapp, temp_repo, qtbot):
    window = NoteWindow()
    qtbot.addWidget(window)
    controller = NoteController(view=window, repository=temp_repo)

    note_to_delete_id = controller.current_note.id
    assert note_to_delete_id is not None

    controller.delete_note_by_id(note_to_delete_id)

    notes = temp_repo.get_all_notes()
    assert len([n for n in notes if n.id == note_to_delete_id]) == 0


def test_theme_switch_context_menu(qapp, temp_repo, qtbot):
    window = NoteWindow()
    qtbot.addWidget(window)
    controller = NoteController(view=window, repository=temp_repo)

    window._on_theme_selected("lavender")
    assert window.current_theme_name == "lavender"
    assert controller.current_note.theme == "lavender"


def test_status_badge_auto_hide(qapp, temp_repo, qtbot):
    window = NoteWindow()
    qtbot.addWidget(window)
    window.show()
    controller = NoteController(view=window, repository=temp_repo)

    window.set_status_text("Guardando...")
    assert not window.status_badge.isHidden()

    window.set_status_text("Guardado")
    assert not window.status_badge.isHidden()

    qtbot.wait(1700)
    assert window.status_badge.isHidden()


def test_controller_math_notes_and_tags(qapp, temp_repo, qtbot):
    window = NoteWindow()
    qtbot.addWidget(window)
    auth = AuthService(override_auth=True)
    controller = NoteController(view=window, repository=temp_repo, auth_service=auth)

    window.content_edit.setPlainText("150 + 50 =\n#idea")
    qtbot.wait(600)

    assert "150 + 50 = 200" in window.content_edit.toPlainText()

    notes = temp_repo.get_all_notes()
    assert len(notes) >= 1
    assert "idea" in notes[0].extract_hashtags()


def test_controller_pin_and_lock(qapp, temp_repo, qtbot):
    window = NoteWindow()
    qtbot.addWidget(window)
    auth = AuthService(override_auth=True)
    controller = NoteController(view=window, repository=temp_repo, auth_service=auth)

    controller.toggle_pin_current_note()
    assert controller.current_note.pinned is True

    controller.toggle_lock_current_note()
    assert controller.current_note.is_locked is True
