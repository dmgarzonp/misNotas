"""Unit tests for Note model and NoteRepository persistence."""

import os
import tempfile
import pytest

from src.models.note_model import Note, NoteRepository


@pytest.fixture
def temp_repo():
    """Provides a NoteRepository linked to a temporary SQLite database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    repo = NoteRepository(db_path)
    yield repo
    if os.path.exists(db_path):
        os.remove(db_path)


def test_note_display_title_explicit():
    note = Note(title="Mi Título Específico", content="Algún contenido aquí")
    assert note.display_title == "Mi Título Específico"


def test_note_display_title_fallback_content():
    note = Note(title="", content="Primera línea del contenido\nSegunda línea")
    assert note.display_title == "Primera línea del contenido"


def test_note_display_title_empty_fallback():
    note = Note(title="", content="")
    assert note.display_title == "Nueva Nota"


def test_create_and_get_note(temp_repo):
    note = temp_repo.create_note(
        title="Nota 1", content="Contenido 1", theme="lavender"
    )
    assert note.id is not None
    assert note.title == "Nota 1"
    assert note.content == "Contenido 1"
    assert note.theme == "lavender"
    assert note.pinned is True

    fetched = temp_repo.get_note_by_id(note.id)
    assert fetched is not None
    assert fetched.id == note.id
    assert fetched.title == "Nota 1"
    assert fetched.pinned is True


def test_update_note(temp_repo):
    note = temp_repo.create_note(title="Original", content="Original Content")
    updated = temp_repo.update_note(
        note_id=note.id,
        title="Actualizado",
        content="Nuevo contenido",
        theme="mint",
        pinned=True,
    )
    assert updated is not None
    assert updated.title == "Actualizado"
    assert updated.theme == "mint"
    assert updated.pinned is True


def test_delete_note(temp_repo):
    note = temp_repo.create_note(title="Eliminar", content="A ser borrada")
    assert temp_repo.delete_note(note.id) is True
    assert temp_repo.get_note_by_id(note.id) is None


def test_get_all_notes_ordering(temp_repo):
    n1 = temp_repo.create_note(title="Nota Normal", content="")
    n2 = temp_repo.create_note(title="Nota Fijada", content="")
    temp_repo.update_note(
        note_id=n2.id, title=n2.title, content=n2.content, pinned=True
    )

    notes = temp_repo.get_all_notes()
    assert len(notes) == 2
    assert notes[0].id == n2.id  # Pinned note comes first


def test_note_geometry_persistence(temp_repo):
    note = temp_repo.create_note(
        title="Nota Geometría", content="Prueba", width=450, height=350
    )
    assert note.width == 450
    assert note.height == 350

    fetched = temp_repo.get_note_by_id(note.id)
    assert fetched is not None
    assert fetched.width == 450
    assert fetched.height == 350

    updated = temp_repo.update_note(
        note_id=note.id,
        title="Nota Geometría",
        content="Prueba Modificada",
        width=520,
        height=410,
    )
    assert updated is not None
    assert updated.width == 520
    assert updated.height == 410


def test_note_position_pos_x_pos_y_persistence(temp_repo):
    note = temp_repo.create_note(
        title="Nota Posición",
        content="Prueba",
        width=400,
        height=300,
        pos_x=250,
        pos_y=180,
    )
    assert note.pos_x == 250
    assert note.pos_y == 180

    fetched = temp_repo.get_note_by_id(note.id)
    assert fetched is not None
    assert fetched.pos_x == 250
    assert fetched.pos_y == 180

    updated = temp_repo.update_note(
        note_id=note.id,
        title="Nota Posición",
        content="Prueba Modificada",
        width=400,
        height=300,
        pos_x=500,
        pos_y=320,
    )
    assert updated is not None
    assert updated.pos_x == 500
    assert updated.pos_y == 320


def test_inote_repository_interface_compliance(temp_repo):
    from src.interfaces.note_repository import INoteRepository

    assert isinstance(temp_repo, INoteRepository)


def test_qstandardpaths_default_db_location():
    from src.models.note_model import get_default_db_path

    db_path = get_default_db_path()
    assert db_path.endswith("mis_apuntes.db")
