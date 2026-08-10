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


def test_single_window_delete_loads_next_note(qapp, temp_repo, qtbot):
    # Create two notes in repository
    n1 = temp_repo.create_note(title="Nota 1", content="Contenido 1")
    n2 = temp_repo.create_note(title="Nota 2", content="Contenido 2")

    window = NoteWindow()
    qtbot.addWidget(window)
    controller = NoteController(view=window, repository=temp_repo, note_id=n1.id)

    assert controller.current_note.id == n1.id

    # Delete active note n1 in single window mode
    controller.delete_note_by_id(n1.id)

    # Window should remain open and load n2
    assert len(NoteController._active_controllers) == 1
    assert controller.current_note is not None
    assert controller.current_note.id == n2.id


def test_sidebar_delete_signal(qapp, temp_repo, qtbot):
    n1 = temp_repo.create_note(title="Nota A", content="Contenido A")
    n2 = temp_repo.create_note(title="Nota B", content="Contenido B")

    window = NoteWindow()
    qtbot.addWidget(window)
    controller = NoteController(view=window, repository=temp_repo, note_id=n1.id)

    # Simulate sidebar delete_note_requested signal
    window.sidebar.delete_note_requested.emit(n2.id)

    notes = temp_repo.get_all_notes()
    assert len([n for n in notes if n.id == n2.id]) == 0
    assert controller.current_note.id == n1.id


def test_tray_signal_single_dispatch(qapp, temp_repo, qtbot):
    from src.services.global_shortcut import QuickNoteManager

    tray_manager = QuickNoteManager(qapp)
    n1 = temp_repo.create_note(title="Nota Base", content="Contenido Base")

    w1 = NoteWindow()
    qtbot.addWidget(w1)
    c1 = NoteController(
        view=w1, repository=temp_repo, tray_manager=tray_manager, note_id=n1.id
    )

    w2 = NoteWindow()
    qtbot.addWidget(w2)
    _ = c1.spawn_new_note_window()

    initial_ctrl_count = len(NoteController._active_controllers)

    # Trigger quick note requested from tray manager
    tray_manager.quick_note_requested.emit()

    # Should spawn EXACTLY ONE additional window (not N windows)
    assert len(NoteController._active_controllers) == initial_ctrl_count + 1


def test_window_resize_persists_in_db(qapp, temp_repo, qtbot):
    n1 = temp_repo.create_note(title="Nota Resize", content="Contenido")
    window = NoteWindow()
    qtbot.addWidget(window)
    controller = NoteController(view=window, repository=temp_repo, note_id=n1.id)

    window.resize(480, 360)
    qtbot.wait(600)

    saved_note = temp_repo.get_note_by_id(n1.id)
    assert saved_note is not None
    assert saved_note.width == 480
    assert saved_note.height == 360


def test_startup_pinned_notes(qapp, temp_repo, qtbot):
    n1 = temp_repo.create_note(title="Fijada 1", content="Text 1")
    n2 = temp_repo.create_note(title="Fijada 2", content="Text 2")
    n3 = temp_repo.create_note(title="Normal", content="Text 3")

    temp_repo.update_note(
        note_id=n1.id, title=n1.title, content=n1.content, pinned=True
    )
    temp_repo.update_note(
        note_id=n2.id, title=n2.title, content=n2.content, pinned=True
    )

    w = NoteWindow()
    qtbot.addWidget(w)
    _ = NoteController(view=w, repository=temp_repo)

    # All active controllers should display pinned notes
    active_ids = {
        c.current_note.id for c in NoteController._active_controllers if c.current_note
    }
    assert n1.id in active_ids
    assert n2.id in active_ids


def test_tray_menu_multiple_notes_update_and_delete(qapp, temp_repo, qtbot):
    from src.services.global_shortcut import QuickNoteManager

    tray_manager = QuickNoteManager(qapp)
    w = NoteWindow()
    qtbot.addWidget(w)
    controller = NoteController(view=w, repository=temp_repo, tray_manager=tray_manager)

    created_ids = []
    for i in range(5):
        note = temp_repo.create_note(
            title=f"Nota {i + 1}", content=f"Contenido {i + 1}"
        )
        created_ids.append(note.id)

    controller.refresh_sidebar()

    menu_actions = tray_manager.menu.actions()
    all_notes_menu = None
    for action in menu_actions:
        if action.menu() and "Todas las Notas" in action.text():
            all_notes_menu = action.menu()
            break

    assert all_notes_menu is not None
    assert len(all_notes_menu.actions()) == 6

    delete_target_id = created_ids[0]
    controller.delete_note_by_id(delete_target_id)

    updated_actions = tray_manager.menu.actions()
    updated_all_notes_menu = None
    for action in updated_actions:
        if action.menu() and "Todas las Notas" in action.text():
            updated_all_notes_menu = action.menu()
            break

    assert updated_all_notes_menu is not None
    assert len(updated_all_notes_menu.actions()) == 5


def test_clipboard_image_paste(qapp, temp_repo, qtbot):
    from PyQt6.QtCore import QMimeData
    from PyQt6.QtGui import QColor, QImage

    img = QImage(100, 100, QImage.Format.Format_ARGB32)
    img.fill(QColor("red"))

    mime_data = QMimeData()
    mime_data.setImageData(img)

    window = NoteWindow()
    qtbot.addWidget(window)
    _ = NoteController(view=window, repository=temp_repo)

    window.content_edit.insertFromMimeData(mime_data)
    qtbot.wait(100)

    html = window.get_content_html()
    assert "<img src=" in html


def test_apply_handwritten_font(qapp, temp_repo, qtbot):
    window = NoteWindow()
    qtbot.addWidget(window)
    _ = NoteController(view=window, repository=temp_repo)

    font_str = "Caveat, Dancing Script, Segoe Script, Comic Sans MS, cursive"
    window._apply_font_family(font_str)
    cursor = window.content_edit.textCursor()
    font_family = cursor.charFormat().fontFamily()
    assert "Caveat" in font_family
