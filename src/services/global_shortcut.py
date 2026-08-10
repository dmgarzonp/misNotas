import logging
from typing import List, Optional
from PyQt6.QtCore import QObject, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QDesktopServices,
    QIcon,
    QPainter,
    QPixmap,
)
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from src.models.note_model import Note
from src.services.autostart_service import AutostartService
from src.services.update_service import UpdateService
from src.views.note_window import DropletMenu
from src.views.styles import get_gnome_icon

logger = logging.getLogger("mis_apuntes.tray")


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
        self.menu: DropletMenu = DropletMenu()
        self.current_menu: DropletMenu = self.menu
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
            logger.warning(
                "System Tray no está disponible en este entorno de escritorio."
            )
            return

        icon = QIcon.fromTheme(
            "accessories-text-editor-symbolic", QIcon(self._create_default_pixmap())
        )
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Mis Apuntes - Notas Rápidas")
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
        logger.info("Icono del System Tray iniciado exitosamente.")

    def update_tray_menu(
        self, notes: List[Note], current_note_id: Optional[int] = None
    ) -> None:
        """Rebuilds DropletMenu for system tray with native GNOME icons and direct delete actions."""
        if not self.menu:
            return

        # Re-use persistent QMenu instance to preserve DBus AppIndicator proxy connection
        self.menu.clear()
        logger.info("Actualizando menú del System Tray con %d notas...", len(notes))

        # GNOME Symbolic Icons
        new_icon = get_gnome_icon("document-new-symbolic")
        pinned_icon = get_gnome_icon("pin-symbolic")
        notes_icon = get_gnome_icon("text-x-generic-symbolic")
        open_icon = get_gnome_icon("document-open-symbolic")
        delete_icon = get_gnome_icon("user-trash-symbolic")
        tag_icon = get_gnome_icon("tag-symbolic")
        quit_icon = get_gnome_icon("application-exit-symbolic")

        # Action 1: New Quick Note (Ctrl+A)
        new_action = self.menu.addAction(new_icon, "Nueva Nota Rápida (Ctrl+A)")
        if new_action:
            new_action.triggered.connect(
                lambda checked=False: self.quick_note_requested.emit()
            )

        self.menu.addSeparator()

        # Pinned Notes Section
        pinned_notes = [n for n in notes if n.pinned and n.id is not None]
        if pinned_notes:
            pinned_menu = self.menu.addMenu(pinned_icon, "Notas Fijadas")
            if pinned_menu:
                for note in pinned_notes:
                    note_id = note.id
                    act = pinned_menu.addAction(pinned_icon, note.display_title)
                    if act and note_id:
                        act.triggered.connect(
                            lambda checked=False, nid=note_id: self.note_selected.emit(
                                nid
                            )
                        )

        # All Notes Section
        all_menu = self.menu.addMenu(notes_icon, f"Todas las Notas ({len(notes)})")
        if all_menu:
            for note in notes:
                if note.id is None:
                    continue
                note_id = note.id
                item_icon = (
                    get_gnome_icon("system-lock-screen-symbolic")
                    if note.is_locked
                    else (pinned_icon if note.pinned else notes_icon)
                )

                # Submenu for each note with Open & Delete actions
                sub_note_menu = all_menu.addMenu(item_icon, note.display_title)
                if sub_note_menu:
                    open_act = sub_note_menu.addAction(open_icon, "Abrir Nota")
                    if open_act:
                        open_act.triggered.connect(
                            lambda checked=False, nid=note_id: self.note_selected.emit(
                                nid
                            )
                        )

                    del_act = sub_note_menu.addAction(delete_icon, "Eliminar Nota")
                    if del_act:
                        del_act.triggered.connect(
                            lambda checked=False, nid=note_id: (
                                self.note_delete_requested.emit(nid)
                            )
                        )

        # Tags Section
        all_tags = sorted(list({t for n in notes for t in n.extract_hashtags()}))
        if all_tags:
            tags_menu = self.menu.addMenu(tag_icon, "Etiquetas (#hashtags)")
            if tags_menu:
                clear_act = tags_menu.addAction(notes_icon, "Mostrar Todas")
                if clear_act:
                    clear_act.triggered.connect(
                        lambda checked=False: self.tag_selected.emit("")
                    )
                tags_menu.addSeparator()
                for tag in all_tags:
                    act = tags_menu.addAction(tag_icon, f"#{tag}")
                    if act:
                        act.triggered.connect(
                            lambda checked=False, t=tag: self.tag_selected.emit(t)
                        )

        self.menu.addSeparator()

        # System Options: Autostart & Updates
        autostart_icon = get_gnome_icon("emblem-system-symbolic")
        update_icon = get_gnome_icon("software-update-available-symbolic")

        autostart_service = AutostartService()
        autostart_action = self.menu.addAction(
            autostart_icon, "⚙️ Iniciar con Ubuntu (Autostart)"
        )
        if autostart_action:
            autostart_action.setCheckable(True)
            autostart_action.setChecked(autostart_service.is_autostart_enabled())
            autostart_action.triggered.connect(self._toggle_autostart)

        update_action = self.menu.addAction(update_icon, "🔄 Buscar Actualizaciones...")
        if update_action:
            update_action.triggered.connect(self._on_check_updates)

        self.menu.addSeparator()

        # Exit Action
        quit_action = self.menu.addAction(quit_icon, "Salir")
        app = QApplication.instance()
        if quit_action and app:
            quit_action.triggered.connect(app.quit)

    def _toggle_autostart(self, checked: bool) -> None:
        """Toggles system autostart entry."""
        autostart_service = AutostartService()
        if checked:
            autostart_service.enable_autostart()
        else:
            autostart_service.disable_autostart()

    def _on_check_updates(self) -> None:
        """Triggers asynchronous update check worker."""
        self._update_service = UpdateService()
        self._update_service.check_for_updates(
            on_found=self._on_update_found,
            on_up_to_date=self._on_up_to_date,
            on_error=self._on_update_error,
        )

    def _on_update_found(self, latest_version: str, html_url: str) -> None:
        """Displays update dialog when a newer version is found."""
        reply = QMessageBox.question(
            None,
            "Nueva Actualización Disponible",
            f"¡Hay una nueva versión de Mis Apuntes disponible! (v{latest_version})\n\n¿Deseas abrir la página de descargas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(html_url))

    def _on_up_to_date(self) -> None:
        """Notifies user that application is up to date."""
        QMessageBox.information(
            None,
            "Mis Apuntes",
            "Tu aplicación Mis Apuntes ya está actualizada a la última versión.",
        )

    def _on_update_error(self, err_msg: str) -> None:
        """Handles update check errors gracefully."""
        logger.warning("Error al comprobar actualizaciones: %s", err_msg)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Pops up DropletMenu at cursor position when tray icon is clicked."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.menu:
                self.menu.exec(QCursor.pos())
