"""Controller layer for Mis Apuntes application.

Connects NoteWindow view signals, QuickNoteManager system tray, MathEvaluator, AuthService,
ImageManager, PDFExporter, and NoteRepository model operations.
"""

import os
import logging
from typing import List, Optional, Set
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from src.interfaces.note_repository import INoteRepository
from src.interfaces.services import IAuthService, IImageManager
from src.models.note_model import Note, NoteRepository
from src.services.auth_service import AuthService
from src.services.global_shortcut import QuickNoteManager
from src.services.image_manager import ImageManager
from src.services.math_evaluator import MathEvaluator
from src.services.pdf_exporter import PDFExporter
from src.views.note_window import NoteWindow

logger = logging.getLogger("mis_apuntes.controller")


class NoteController(QObject):
    """Controller managing a single NoteWindow instance and active Note entity in a multi-window app."""

    note_deleted = pyqtSignal(int)
    note_created = pyqtSignal(int)

    # Active Controllers Registry for Multi-Window Sticky Notes
    _active_controllers: List["NoteController"] = []
    _shared_tray_manager: Optional[QuickNoteManager] = None
    _tray_connected: bool = False

    @classmethod
    def set_tray_manager(cls, tray_manager: QuickNoteManager) -> None:
        """Attaches and connects QuickNoteManager signals globally to class handlers exactly once."""
        cls._shared_tray_manager = tray_manager
        if not cls._tray_connected:
            tray_manager.quick_note_requested.connect(cls._on_tray_quick_note)
            tray_manager.note_selected.connect(cls._on_tray_note_selected)
            tray_manager.note_delete_requested.connect(cls._on_tray_note_delete)
            tray_manager.tag_selected.connect(cls._on_tray_tag_selected)
            cls._tray_connected = True

        try:
            repo = NoteRepository()
            notes = repo.get_all_notes()
            tray_manager.update_tray_menu(notes, None)
        except Exception:
            pass

    @classmethod
    def _on_tray_quick_note(cls) -> None:
        """Handles tray quick note request exactly once across active controllers."""
        if cls._active_controllers:
            cls._active_controllers[-1].spawn_new_note_window()
        else:
            repo = NoteRepository()
            new_note = repo.create_note(title="", content="", theme="honey")
            view = NoteWindow()
            ctrl = NoteController(
                view=view,
                repository=repo,
                tray_manager=cls._shared_tray_manager,
                note_id=new_note.id,
            )
            view.show()
            view.raise_()
            view.activateWindow()

    @classmethod
    def _on_tray_note_selected(cls, note_id: int) -> None:
        """Handles tray note selection request exactly once across active controllers."""
        if cls._active_controllers:
            cls._active_controllers[-1].load_note(note_id)
        else:
            repo = NoteRepository()
            view = NoteWindow()
            ctrl = NoteController(
                view=view,
                repository=repo,
                tray_manager=cls._shared_tray_manager,
                note_id=note_id,
            )
            view.show()
            view.raise_()
            view.activateWindow()

    @classmethod
    def _on_tray_note_delete(cls, note_id: int) -> None:
        """Handles tray note delete request exactly once across active controllers."""
        if cls._active_controllers:
            cls._active_controllers[-1].delete_note_by_id(note_id)
        else:
            repo = NoteRepository()
            repo.delete_note(note_id)
            if cls._shared_tray_manager:
                cls._shared_tray_manager.update_tray_menu(repo.get_all_notes(), None)

    @classmethod
    def _on_tray_tag_selected(cls, tag: str) -> None:
        """Handles tray tag selection request exactly once across active controllers."""
        if cls._active_controllers:
            cls._active_controllers[-1].filter_by_tag(tag)

    def __init__(
        self,
        view: NoteWindow,
        repository: INoteRepository,
        auth_service: Optional[IAuthService] = None,
        tray_manager: Optional[QuickNoteManager] = None,
        image_manager: Optional[IImageManager] = None,
        note_id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.view = view
        self.repository = repository
        self.auth_service = auth_service or AuthService()
        self.tray_manager = tray_manager or NoteController._shared_tray_manager
        if tray_manager:
            NoteController.set_tray_manager(tray_manager)
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
        """Subscribes to NoteWindow UI signals."""
        self.view.title_changed.connect(self._on_title_changed)
        self.view.content_changed.connect(self._on_content_changed)
        self.view.theme_changed.connect(self._on_theme_changed)
        self.view.background_style_changed.connect(self._on_background_style_changed)
        self.view.window_resized.connect(self._on_window_resized)
        self.view.window_moved.connect(self._on_window_moved)
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
        self.view.sidebar.delete_note_requested.connect(self.delete_note_by_id)
        self.view.sidebar.tag_selected.connect(self.filter_by_tag)
        self.view.sidebar.search_changed.connect(self.filter_by_search)

    def _load_or_create_default_note(self) -> None:
        """Loads pinned notes or latest existing note, or creates a new default note."""
        notes = self.repository.get_all_notes()
        if not notes:
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
            return

        pinned_notes = [n for n in notes if n.pinned and n.id is not None]
        if pinned_notes:
            self.load_note(pinned_notes[0].id)  # type: ignore
            for p_note in pinned_notes[1:]:
                if p_note.id is not None:
                    already_open = any(
                        ctrl.current_note and ctrl.current_note.id == p_note.id
                        for ctrl in NoteController._active_controllers
                    )
                    if not already_open:
                        new_view = NoteWindow()
                        NoteController(
                            view=new_view,
                            repository=self.repository,
                            auth_service=self.auth_service,
                            tray_manager=self.tray_manager,
                            image_manager=self.image_manager,
                            note_id=p_note.id,
                        )
                        new_view.show()
        elif notes[0].id is not None:
            self.load_note(notes[0].id)

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
        """Loads specific note by ID in current window or brings existing open window to front."""
        # Check if another open window is already displaying this note
        for ctrl in NoteController._active_controllers:
            if ctrl != self and ctrl.current_note and ctrl.current_note.id == note_id:
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

        # Save current note before switching
        if self.current_note and self.current_note.id != note_id:
            self.save_timer.stop()
            self._save_current_note()

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
                width=self.current_note.width,
                height=self.current_note.height,
                pos_x=self.current_note.pos_x,
                pos_y=self.current_note.pos_y,
            )
            self.view.set_status_text("Guardado")

    def _on_window_resized(self, width: int, height: int) -> None:
        """Handles window resize events, updates current_note geometry, and triggers save timer."""
        if self.current_note:
            if self.current_note.width != width or self.current_note.height != height:
                self.current_note.width = width
                self.current_note.height = height
                self.save_timer.start()

    def _on_window_moved(self, pos_x: int, pos_y: int) -> None:
        """Handles window move/drag events, updates current_note desktop position, and triggers save timer."""
        if (
            self.current_note
            and getattr(self.view, "_is_initialized", False)
            and self.view.isVisible()
        ):
            if pos_x >= 0 and pos_y >= 0:
                if self.current_note.pos_x != pos_x or self.current_note.pos_y != pos_y:
                    self.current_note.pos_x = pos_x
                    self.current_note.pos_y = pos_y
                    self.save_timer.start()

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
        tray = NoteController._shared_tray_manager or self.tray_manager
        if tray:
            tray.update_tray_menu(notes, current_id)

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

        curr_w = self.view.width()
        curr_h = self.view.height()
        curr_x = self.view.pos().x()
        curr_y = self.view.pos().y()

        # Prevent overwriting valid coordinates with (0,0) during startup mapping
        if curr_x <= 0 and curr_y <= 0 and self.current_note.pos_x > 0:
            curr_x = self.current_note.pos_x
            curr_y = self.current_note.pos_y

        if self.current_note.id is None:
            created = self.repository.create_note(
                title=self.current_note.title,
                content=self.current_note.content,
                content_html=self.view.get_content_html(),
                theme=self.current_note.theme,
                background_style=self.current_note.background_style,
                width=curr_w,
                height=curr_h,
                pos_x=curr_x,
                pos_y=curr_y,
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
                width=curr_w,
                height=curr_h,
                pos_x=curr_x,
                pos_y=curr_y,
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
        tray = NoteController._shared_tray_manager or self.tray_manager
        if tray:
            notes = self.repository.get_all_notes()
            curr_id = self.current_note.id if self.current_note else None
            tray.update_tray_menu(notes, curr_id)

    def spawn_new_note_window(self) -> "NoteController":
        """Spawns a NEW separate floating NoteWindow side-by-side to active note window."""
        self.save_timer.stop()
        self._save_current_note()

        # Calculate position offset side-by-side
        curr_pos = self.view.pos()
        curr_x = curr_pos.x() if curr_pos.x() > 0 else 100
        curr_y = curr_pos.y() if curr_pos.y() > 0 else 100

        new_x = curr_x + 320
        new_y = curr_y

        if new_x > 1200:
            new_x = 100
            new_y = curr_y + 300

        # Create new note entity in database with explicit side-by-side coordinates
        new_note = self.repository.create_note(
            title="",
            content="",
            content_html="",
            theme=self.current_note.theme if self.current_note else "honey",
            background_style=(
                self.current_note.background_style if self.current_note else "blank"
            ),
            width=300,
            height=280,
            pos_x=new_x,
            pos_y=new_y,
            pinned=True,
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

        new_view.show()
        new_view.raise_()
        new_view.activateWindow()

        self._notify_all_controllers()
        return new_controller

    def close_window(self) -> None:
        """Closes current window, saves pending changes, and unregisters controller."""
        self.save_timer.stop()
        self._save_current_note()
        if self in NoteController._active_controllers:
            NoteController._active_controllers.remove(self)
        try:
            self.view.close()
        except Exception:
            pass

    def delete_note_by_id(self, note_id: int) -> None:
        """Deletes note permanently from SQLite database and updates all UI lists and tray menu."""
        existing = self.repository.get_note_by_id(note_id)
        if not existing:
            self._notify_all_controllers()
            return

        controllers_viewing_note = [
            ctrl
            for ctrl in list(NoteController._active_controllers)
            if ctrl.current_note and ctrl.current_note.id == note_id
        ]
        for ctrl in controllers_viewing_note:
            ctrl.save_timer.stop()

        # Permanently delete from SQLite DB
        self.repository.delete_note(note_id)

        # Handle windows displaying the deleted note
        for ctrl in controllers_viewing_note:
            if len(NoteController._active_controllers) <= 1:
                ctrl.current_note = None
                notes = ctrl.repository.get_all_notes()
                if notes and notes[0].id is not None:
                    ctrl.load_note(notes[0].id)
                else:
                    ctrl._load_or_create_default_note()
            else:
                ctrl.current_note = None
                ctrl.close_window()

        self.note_deleted.emit(note_id)
        self._notify_all_controllers()

    def delete_current_note(self) -> None:
        """Deletes current note after user confirmation and loads next note or closes window."""
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
