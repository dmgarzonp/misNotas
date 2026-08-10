"""Global Quick Note and System Tray service for Mis Apuntes application.

Provides system tray integration using DropletMenu with top drop tail arrow,
direct note deletion, full note listing, and hashtag filtering.
"""

from typing import List, Optional
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QCursor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.models.note_model import Note
from src.views.note_window import DropletMenu
from src.views.styles import get_gnome_icon


class QuickNoteManager(QObject):
    """Manages system tray icon using DropletMenu popup with top droplet pointer arrow."""

    quick_note_requested = pyqtSignal()
    show_main_requested = pyqtSignal()
    note_selected = pyqtSignal(int)
    note_delete_requested = pyqtSignal(int)
    tag_selected = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self.current_menu: Optional[DropletMenu] = None
        self._init_tray()

    def _create_default_pixmap(self) -> QPixmap:
        """Generates a clean macOS yellow note icon pixmap fallback."""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#FBBF24"))
        painter.setPen(QColor("#B45309"))
        painter.drawRoundedRect(2, 2, 20, 20, 5, 5)
        painter.end()
        return pixmap

    def _init_tray(self) -> None:
        """Initializes system tray icon using native GNOME symbolic icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = QIcon.fromTheme(
            "accessories-text-editor-symbolic", QIcon(self._create_default_pixmap())
        )
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Mis Apuntes - Notas Rápidas")
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def update_tray_menu(
        self, notes: List[Note], current_note_id: Optional[int] = None
    ) -> None:
        """Rebuilds DropletMenu for system tray with native GNOME icons and direct delete actions."""
        if not self.tray_icon:
            return

        tray_menu = DropletMenu()

        # Action: New Quick Note (Ctrl+A)
        new_icon = get_gnome_icon("document-new-symbolic")
        new_action = QAction(new_icon, "Nueva Nota Rápida (Ctrl+A)", self)
        new_action.triggered.connect(self.quick_note_requested.emit)
        tray_menu.addAction(new_action)

        tray_menu.addSeparator()

        # Pinned Notes Submenu / Section
        pinned_notes = [n for n in notes if n.pinned and n.id is not None]
        if pinned_notes:
            pinned_icon = get_gnome_icon("pin-symbolic")
            pinned_menu = tray_menu.addMenu(pinned_icon, "Notas Fijadas")
            if pinned_menu:
                for note in pinned_notes:
                    note_id = note.id
                    act = QAction(pinned_icon, note.display_title, self)
                    if note_id:
                        act.triggered.connect(
                            lambda checked, nid=note_id: self.note_selected.emit(nid)
                        )
                    pinned_menu.addAction(act)

        # All Notes Submenu with Sub-Actions (Open & Delete)
        notes_icon = get_gnome_icon("text-x-generic-symbolic")
        delete_icon = get_gnome_icon("user-trash-symbolic")
        all_menu = tray_menu.addMenu(notes_icon, "Todas las Notas")
        if all_menu:
            for note in notes:
                if note.id is None:
                    continue
                note_id = note.id
                item_icon = (
                    get_gnome_icon("system-lock-screen-symbolic")
                    if note.is_locked
                    else (get_gnome_icon("pin-symbolic") if note.pinned else notes_icon)
                )
                active_str = " (Activa)" if note_id == current_note_id else ""

                # Note Submenu with Open & Delete actions
                sub_note_menu = all_menu.addMenu(
                    item_icon, f"{note.display_title}{active_str}"
                )
                if sub_note_menu:
                    open_act = QAction(item_icon, "Abrir Nota", self)
                    open_act.triggered.connect(
                        lambda checked, nid=note_id: self.note_selected.emit(nid)
                    )
                    sub_note_menu.addAction(open_act)

                    del_act = QAction(delete_icon, "Eliminar Nota", self)
                    del_act.triggered.connect(
                        lambda checked, nid=note_id: self.note_delete_requested.emit(
                            nid
                        )
                    )
                    sub_note_menu.addAction(del_act)

        # Tags Submenu
        all_tags = sorted(list({t for n in notes for t in n.extract_hashtags()}))
        if all_tags:
            tag_icon = get_gnome_icon("tag-symbolic")
            tags_menu = tray_menu.addMenu(tag_icon, "Etiquetas (#hashtags)")
            if tags_menu:
                clear_act = QAction("Mostrar Todas", self)
                clear_act.triggered.connect(lambda: self.tag_selected.emit(""))
                tags_menu.addAction(clear_act)
                tags_menu.addSeparator()
                for tag in all_tags:
                    act = QAction(tag_icon, f"#{tag}", self)
                    act.triggered.connect(
                        lambda checked, t=tag: self.tag_selected.emit(t)
                    )
                    tags_menu.addAction(act)

        tray_menu.addSeparator()

        # Exit Action
        quit_icon = get_gnome_icon("application-exit-symbolic")
        quit_action = QAction(quit_icon, "Salir", self)
        app = QApplication.instance()
        if app:
            quit_action.triggered.connect(app.quit)
        tray_menu.addAction(quit_action)

        self.current_menu = tray_menu
        self.tray_icon.setContextMenu(tray_menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Pops up DropletMenu at cursor position when tray icon is clicked."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.current_menu:
                self.current_menu.exec(QCursor.pos())
