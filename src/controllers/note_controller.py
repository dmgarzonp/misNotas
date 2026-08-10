"""Controller layer for Mis Apuntes application.

Connects NoteWindow view signals, QuickNoteManager system tray, MathEvaluator, AuthService,
ImageManager, PDFExporter, and NoteRepository model operations.
"""

import os
from typing import List, Optional, Set
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from src.models.note_model import Note, NoteRepository
from src.services.auth_service import AuthService
from src.services.global_shortcut import QuickNoteManager
from src.services.image_manager import ImageManager
from src.services.math_evaluator import MathEvaluator
from src.services.pdf_exporter import PDFExporter
from src.views.note_window import NoteWindow


class NoteController(QObject):
    """Controller managing a single NoteWindow instance and active Note entity in a multi-window app."""

    note_deleted = pyqtSignal(int)
    note_created = pyqtSignal(int)

    # Active Controllers Registry for Multi-Window Sticky Notes
    _active_controllers: List["NoteController"] = []

    def __init__(
        self,
        view: NoteWindow,
        repository: NoteRepository,
        auth_service: Optional[AuthService] = None,
        tray_manager: Optional[QuickNoteManager] = None,
        image_manager: Optional[ImageManager] = None,
        note_id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.view = view
        self.repository = repository
        self.auth_service = auth_service or AuthService()
        self.tray_manager = tray_manager
        self.image_manager = image_manager or ImageManager()
        self.math_evaluator = MathEvaluator()

        self.current_note: Optional[Note] = None
        self.current_tag_filter: Optional[str] = None
        self.search_query: str = ""

        # Register active controller
        if self not in NoteController._active_controllers:
            NoteController._active_controllers.append(self)

        # Setup Debounce Timer for Auto-Save (500ms delay)
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(500)
        self.save_timer.timeout.connect(self._save_current_note)

        # Global & Local New Note Shortcut (Ctrl+A)
        self.quick_shortcut = QShortcut(QKeySequence("Ctrl+A"), self.view)
        self.quick_shortcut.activated.connect(self.spawn_new_note_window)

        # Connect View Signals
        self._connect_signals()

        # Load initial note or default
        if note_id:
            self.load_note(note_id)
        else:
            self._load_or_create_default_note()

        self.refresh_sidebar()

    def _connect_signals(self) -> None:
        """Subscribes to NoteWindow UI and Tray signals."""
        self.view.title_changed.connect(self._on_title_changed)
        self.view.content_changed.connect(self._on_content_changed)
        self.view.theme_changed.connect(self._on_theme_changed)
        self.view.background_style_changed.connect(self._on_background_style_changed)
        self.view.new_note_requested.connect(self.spawn_new_note_window)
        self.view.delete_note_requested.connect(self.delete_current_note)
        self.view.pin_requested.connect(self.toggle_pin_current_note)
        self.view.lock_requested.connect(self.toggle_lock_current_note)
        self.view.toggle_sidebar_requested.connect(self.toggle_sidebar)
        self.view.close_requested.connect(self.close_window)
        self.view.image_requested.connect(self.choose_and_insert_image)
        self.view.export_pdf_requested.connect(self.export_note_pdf)
        self.view.content_edit.file_dropped.connect(self.handle_dropped_image)

        # Sidebar Signals
        self.view.sidebar.note_selected.connect(self.load_note)
        self.view.sidebar.tag_selected.connect(self.filter_by_tag)
        self.view.sidebar.search_changed.connect(self.filter_by_search)

        # Tray Signals
        if self.tray_manager:
            self.tray_manager.quick_note_requested.connect(self.spawn_new_note_window)
            self.tray_manager.note_selected.connect(self.load_note)
            self.tray_manager.note_delete_requested.connect(self.delete_note_by_id)
            self.tray_manager.tag_selected.connect(self.filter_by_tag)

    def _load_or_create_default_note(self) -> None:
        """Loads latest existing note or creates a new default note with empty title for placeholder."""
        notes = self.repository.get_all_notes()
        if notes:
            self.load_note(notes[0].id)  # type: ignore
        else:
            self.current_note = self.repository.create_note(
                title="",
                content="Esta es tu primera nota rápida al estilo macOS Sequoia.\n\n"
                "• Presiona Ctrl+A para crear una NUEVA nota flotante al lado.\n"
                "• Escribe operaciones matemáticas en tiempo real: 125 + 45 = \n"
                "• Clic derecho para cambiar tipografías, insertar imágenes o exportar a PDF.\n\n"
                "#bienvenida #ideas",
                theme="honey",
            )
            self._sync_view_with_model()

    def choose_and_insert_image(self) -> None:
        """Opens QFileDialog to select an image, imports it to local storage, and inserts HTML into editor."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Seleccionar Imagen",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.gif *.svg *.webp)",
        )
        if file_path:
            file_url = self.image_manager.import_image(file_path)
            if file_url:
                self.view.insert_image_html(file_url)

    def handle_dropped_image(self, file_path: str) -> None:
        """Handles image dropped onto editor, copying it into local assets storage."""
        file_url = self.image_manager.import_image(file_path)
        if file_url:
            self.view.insert_image_html(file_url)

    def export_note_pdf(self) -> None:
        """Opens QFileDialog to choose output PDF destination and exports styled note."""
        if not self.current_note:
            return

        default_name = f"{self.current_note.display_title}.pdf"
        output_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Exportar Nota a PDF",
            default_name,
            "Documentos PDF (*.pdf)",
        )
        if output_path:
            success = PDFExporter.export_note_to_pdf(
                title=self.current_note.title,
                content_html=self.view.get_content_html(),
                theme_name=self.current_note.theme,
                output_path=output_path,
            )
            if success:
                QMessageBox.information(
                    self.view,
                    "Exportación Exitosa",
                    f"La nota fue exportada exitosamente a PDF en:\n{output_path}",
                )

    def load_note(self, note_id: int) -> None:
        """Loads specific note by ID and brings its window to front (show, raise, activateWindow)."""
        # Check if an existing open window is already displaying this note
        for ctrl in NoteController._active_controllers:
            if ctrl.current_note and ctrl.current_note.id == note_id:
                ctrl.view.show()
                ctrl.view.raise_()
                ctrl.view.activateWindow()
                return

        note = self.repository.get_note_by_id(note_id)
        if not note:
            return

        # Handle Protected/Locked Note Authentication
        if note.is_locked:
            authenticated = self.auth_service.authenticate_user(
                f"Desbloquear nota '{note.display_title}'"
            )
            if not authenticated:
                QMessageBox.warning(
                    self.view,
                    "Acceso Denegado",
                    "Autenticación fallida o cancelada. La nota permanece bloqueada.",
                )
                return

        # If THIS controller already has an active note, spawn a new window for the requested note
        if self.current_note is not None and self.current_note.id != note_id:
            new_view = NoteWindow()
            new_controller = NoteController(
                view=new_view,
                repository=self.repository,
                auth_service=self.auth_service,
                tray_manager=self.tray_manager,
                image_manager=self.image_manager,
                note_id=note_id,
            )
            new_view.show()
            new_view.raise_()
            new_view.activateWindow()
            self._notify_all_controllers()
            return

        self.current_note = note
        self._sync_view_with_model()
        self.refresh_sidebar()

        self.view.show()
        self.view.raise_()
        self.view.activateWindow()

    def _sync_view_with_model(self) -> None:
        """Updates view controls to match current_note state."""
        if self.current_note:
            self.view.set_note_data(
                title=self.current_note.title,
                content=self.current_note.content,
                content_html=self.current_note.content_html,
                theme_name=self.current_note.theme,
                pinned=self.current_note.pinned,
                is_locked=self.current_note.is_locked,
                background_style=self.current_note.background_style,
            )
            self.view.set_status_text("Guardado")

    def refresh_sidebar(self) -> None:
        """Refreshes sidebar note items, hashtag tags, and system tray menu across all active windows."""
        notes = self.repository.get_all_notes()
        all_tags: Set[str] = set()

        filtered_notes: List[Note] = []
        for note in notes:
            all_tags.update(note.extract_hashtags())

            if (
                self.current_tag_filter
                and self.current_tag_filter not in note.extract_hashtags()
            ):
                continue

            if self.search_query:
                query = self.search_query.lower()
                if (
                    query not in note.title.lower()
                    and query not in note.content.lower()
                ):
                    continue

            filtered_notes.append(note)

        current_id = self.current_note.id if self.current_note else None
        self.view.sidebar.populate_notes(filtered_notes, current_id)
        self.view.sidebar.populate_tags(list(all_tags))

        # Update System Tray Menu
        if self.tray_manager:
            self.tray_manager.update_tray_menu(notes, current_id)

    def filter_by_tag(self, tag: str) -> None:
        """Filters notes list by hashtag."""
        self.current_tag_filter = tag if tag else None
        self.refresh_sidebar()
        self.view.show()
        self.view.raise_()
        self.view.activateWindow()

    def filter_by_search(self, query: str) -> None:
        """Filters sidebar notes list by search text query."""
        self.search_query = query.strip()
        self.refresh_sidebar()

    def toggle_sidebar(self) -> None:
        """Toggles macOS sidebar panel visibility."""
        if self.view.sidebar.isVisible():
            self.view.sidebar.hide()
        else:
            self.refresh_sidebar()
            self.view.sidebar.show()

    def _on_title_changed(self, title: str) -> None:
        """Handles title text changes and triggers debounced save timer."""
        if self.current_note:
            self.current_note.title = title
            self.view.set_status_text("Guardando...")
            self.save_timer.start()

    def _on_content_changed(self, content: str) -> None:
        """Handles content text changes, processes Math Notes, and triggers save timer."""
        if self.current_note:
            self.current_note.content = content
            self.current_note.content_html = self.view.get_content_html()

            # Process Math Notes Equations (e.g. 120 + 35 =)
            updated_text, math_applied = self.math_evaluator.process_note_text(content)
            if math_applied:
                self.current_note.content = updated_text
                self.view.title_input.blockSignals(True)
                self.view.content_edit.blockSignals(True)
                self.view.content_edit.setPlainText(updated_text)
                self.view.title_input.blockSignals(False)
                self.view.content_edit.blockSignals(False)

            self.view.set_status_text("Guardando...")
            self.save_timer.start()

    def _on_theme_changed(self, theme_name: str) -> None:
        """Handles theme dropdown changes and immediately saves preference."""
        if self.current_note:
            self.current_note.theme = theme_name
            self.save_timer.stop()
            self._save_current_note()

    def _on_background_style_changed(self, style_name: str) -> None:
        """Handles background texture changes."""
        if self.current_note:
            self.current_note.background_style = style_name
            self.save_timer.stop()
            self._save_current_note()

    def toggle_pin_current_note(self) -> None:
        """Toggles pinned status of current note."""
        if self.current_note and self.current_note.id:
            updated = self.repository.toggle_pin(self.current_note.id)
            if updated:
                self.current_note = updated
                self._sync_view_with_model()
                self._notify_all_controllers()

    def toggle_lock_current_note(self) -> None:
        """Toggles password protection on current note using PolicyKit authentication."""
        if not self.current_note or not self.current_note.id:
            return

        action_name = (
            "Quitar protección de" if self.current_note.is_locked else "Proteger"
        )
        authenticated = self.auth_service.authenticate_user(
            f"{action_name} la nota '{self.current_note.display_title}'"
        )
        if authenticated:
            updated = self.repository.toggle_lock(self.current_note.id)
            if updated:
                self.current_note = updated
                self._sync_view_with_model()
                self._notify_all_controllers()
                msg = "Nota protegida" if updated.is_locked else "Protección removida"
                self.view.set_status_text(msg)
        else:
            QMessageBox.warning(
                self.view,
                "Autenticación Fallida",
                "Se requiere la contraseña de usuario para cambiar la protección.",
            )

    def _save_current_note(self) -> None:
        """Persists current note state into SQLite database."""
        if not self.current_note:
            return

        if self.current_note.id is None:
            created = self.repository.create_note(
                title=self.current_note.title,
                content=self.current_note.content,
                content_html=self.view.get_content_html(),
                theme=self.current_note.theme,
                background_style=self.current_note.background_style,
            )
            self.current_note = created
            self.note_created.emit(created.id)
        else:
            updated = self.repository.update_note(
                note_id=self.current_note.id,
                title=self.current_note.title,
                content=self.current_note.content,
                content_html=self.view.get_content_html(),
                theme=self.current_note.theme,
                pinned=self.current_note.pinned,
                is_locked=self.current_note.is_locked,
                background_style=self.current_note.background_style,
            )
            if updated:
                self.current_note = updated

        self.view.set_status_text("Guardado")
        self._notify_all_controllers()

    def _notify_all_controllers(self) -> None:
        """Notifies all active window controllers to refresh sidebars and system tray."""
        valid_controllers: List[NoteController] = []
        for ctrl in list(NoteController._active_controllers):
            if os.path.exists(ctrl.repository.db_path):
                try:
                    ctrl.refresh_sidebar()
                    valid_controllers.append(ctrl)
                except Exception:
                    pass
        NoteController._active_controllers = valid_controllers

        # Always update system tray menu even if no windows are open!
        if self.tray_manager:
            notes = self.repository.get_all_notes()
            curr_id = self.current_note.id if self.current_note else None
            self.tray_manager.update_tray_menu(notes, curr_id)

    def spawn_new_note_window(self) -> "NoteController":
        """Spawns a NEW separate floating NoteWindow next to or below active note window."""
        self.save_timer.stop()
        self._save_current_note()

        # Create new note entity in database
        new_note = self.repository.create_note(
            title="",
            content="",
            content_html="",
            theme=self.current_note.theme if self.current_note else "honey",
            background_style=(
                self.current_note.background_style if self.current_note else "blank"
            ),
        )

        # Spawn new window & controller
        new_view = NoteWindow()
        new_controller = NoteController(
            view=new_view,
            repository=self.repository,
            auth_service=self.auth_service,
            tray_manager=self.tray_manager,
            image_manager=self.image_manager,
            note_id=new_note.id,
        )

        # Position offset relative to active window
        curr_pos = self.view.pos()
        new_view.move(curr_pos.x() + 35, curr_pos.y() + 35)

        new_view.show()
        new_view.raise_()
        new_view.activateWindow()

        self._notify_all_controllers()
        return new_controller

    def close_window(self) -> None:
        """Closes current window and unregisters controller."""
        self.save_timer.stop()
        if self in NoteController._active_controllers:
            NoteController._active_controllers.remove(self)
        self.view.close()

    def delete_note_by_id(self, note_id: int) -> None:
        """Deletes note permanently from SQLite database and updates all UI lists and tray menu."""
        # Unregister and close any open window displaying this note WITHOUT re-saving!
        for ctrl in list(NoteController._active_controllers):
            if ctrl.current_note and ctrl.current_note.id == note_id:
                ctrl.save_timer.stop()
                ctrl.current_note = None
                ctrl.close_window()

        # Permanently delete from SQLite DB
        self.repository.delete_note(note_id)
        self.note_deleted.emit(note_id)

        # Refresh all active controllers AND tray menu
        self._notify_all_controllers()
        if self.tray_manager:
            notes = self.repository.get_all_notes()
            self.tray_manager.update_tray_menu(notes, None)

    def delete_current_note(self) -> None:
        """Deletes current note after user confirmation and closes window."""
        if not self.current_note or self.current_note.id is None:
            return

        reply = QMessageBox.question(
            self.view,
            "Eliminar Nota",
            "¿Estás seguro de que deseas eliminar esta nota permanentemente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            deleted_id = self.current_note.id
            self.delete_note_by_id(deleted_id)
