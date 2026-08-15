import logging
from typing import List, Optional
from PyQt6.QtCore import QObject, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QDesktopServices,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from src.models.note_model import Note
from src.services.autostart_service import AutostartService
from src.services.update_service import UpdateService
from src.views.note_window import DropletMenu
from src.views.styles import get_gnome_icon
from src.views.update_dialog import UpdateDialog

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
        self._update_dialog: Optional[UpdateDialog] = None
        self._update_service: Optional[UpdateService] = None
        self._retry_count: int = 0
        self._init_tray()

    def _create_note_icon(self) -> QIcon:
        """Generates a multi-resolution QIcon with fallbacks to system theme and SVG icon files."""
        # 1. Try system icon theme 'mis-apuntes'
        theme_icon = QIcon.fromTheme("mis-apuntes")
        if not theme_icon.isNull() and len(theme_icon.availableSizes()) > 0:
            return theme_icon

        # 2. Check local SVG paths in data/mis-apuntes.svg
        import os
        import sys

        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        svg_candidates = [
            os.path.join(base_dir, "data", "mis-apuntes.svg"),
            "/usr/share/icons/hicolor/scalable/apps/mis-apuntes.svg",
        ]
        if hasattr(sys, "_MEIPASS"):
            svg_candidates.insert(
                0, os.path.join(sys._MEIPASS, "data", "mis-apuntes.svg")
            )

        for svg_path in svg_candidates:
            if os.path.exists(svg_path):
                svg_icon = QIcon(svg_path)
                if not svg_icon.isNull() and len(svg_icon.availableSizes()) > 0:
                    return svg_icon

        # 3. Procedural QIcon fallback
        icon = QIcon()
        for size in (16, 22, 24, 32, 48, 64):
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Yellow note background
            painter.setBrush(QColor("#FBBF24"))
            painter.setPen(QColor("#B45309"))
            corner = max(2, int(size * 0.15))
            painter.drawRoundedRect(
                1, 1, size - 2, size - 2, float(corner), float(corner)
            )

            # Notebook lines
            if size >= 16:
                line_pen = QPen(QColor("#D97706"), max(1.0, size / 24.0))
                painter.setPen(line_pen)
                y1 = int(size * 0.35)
                y2 = int(size * 0.55)
                y3 = int(size * 0.75)
                margin = int(size * 0.2)
                painter.drawLine(margin, y1, size - margin, y1)
                painter.drawLine(margin, y2, size - margin, y2)
                painter.drawLine(margin, y3, int(size * 0.65), y3)

            painter.end()
            icon.addPixmap(pixmap)
        return icon

    def _init_tray(self) -> None:
        """Initializes system tray icon using custom multi-size QIcon for DBus SNI compatibility."""
        if self.tray_icon is not None:
            return

        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning(
                "System Tray no disponible en este momento. Reintentando..."
            )
            self._schedule_tray_retry()
            return

        icon = self._create_note_icon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Mis Apuntes - Notas Rápidas")
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
        logger.info("Icono del System Tray iniciado exitosamente.")

    def _schedule_tray_retry(self) -> None:
        """Schedules retry attempt if system tray is not immediately available at boot."""
        if self._retry_count < 10 and self.tray_icon is None:
            self._retry_count += 1
            QTimer.singleShot(2000, self._init_tray)

    def update_tray_menu(
        self, notes: List[Note], current_note_id: Optional[int] = None
    ) -> None:
        """Rebuilds DropletMenu for system tray with native GNOME icons and direct delete actions."""
        if self.tray_icon is None:
            self._init_tray()

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

        # System Options: Autostart (standard checkable QAction for DBus AppIndicator compatibility) & Updates
        autostart_icon = get_gnome_icon("system-run-symbolic")
        if autostart_icon.isNull():
            autostart_icon = get_gnome_icon("emblem-system-symbolic")

        update_icon = get_gnome_icon("software-update-available-symbolic")
        if update_icon.isNull():
            update_icon = get_gnome_icon("system-software-update-symbolic")

        autostart_service = AutostartService()
        autostart_action = self.menu.addAction(
            autostart_icon, "Iniciar al arrancar el sistema"
        )
        if autostart_action:
            autostart_action.setCheckable(True)
            autostart_action.setChecked(autostart_service.is_autostart_enabled())
            autostart_action.triggered.connect(self._toggle_autostart)

        update_action = self.menu.addAction(update_icon, "Buscar actualizaciones...")
        if update_action:
            update_action.triggered.connect(self._on_check_updates)

        about_icon = get_gnome_icon("help-about-symbolic")
        if about_icon.isNull():
            about_icon = get_gnome_icon("dialog-information-symbolic")

        about_action = self.menu.addAction(about_icon, "Acerca de Mis Apuntes")
        if about_action:
            about_action.triggered.connect(self._on_show_about)

        self.menu.addSeparator()

        # Exit Action
        quit_action = self.menu.addAction(quit_icon, "Salir")
        app = QApplication.instance()
        if quit_action and app:
            quit_action.triggered.connect(app.quit)

    def _on_show_about(self) -> None:
        """Displays About Dialog modal with version v1.0.1 details."""
        from src.views.about_dialog import AboutDialog

        dialog = AboutDialog()
        dialog.exec()

    def _toggle_autostart(self, checked: bool) -> None:
        """Toggles system autostart entry."""
        autostart_service = AutostartService()
        if checked:
            autostart_service.enable_autostart()
        else:
            autostart_service.disable_autostart()

    def _on_check_updates(self) -> None:
        """Displays UpdateDialog modal and launches background update check worker."""
        if not self._update_dialog:
            self._update_dialog = UpdateDialog()
            self._update_dialog.retry_requested.connect(self._start_update_worker)

        self._update_dialog.set_searching()
        self._update_dialog.show()
        self._update_dialog.raise_()
        self._update_dialog.activateWindow()

        self._start_update_worker()

    def _start_update_worker(self) -> None:
        """Executes background update worker thread."""
        self._update_service = UpdateService()
        self._update_service.check_for_updates(
            on_found=self._on_update_found,
            on_up_to_date=self._on_up_to_date,
            on_error=self._on_update_error,
        )

    def _on_update_found(self, latest_version: str, html_url: str) -> None:
        """Routes update found event to UpdateDialog UI."""
        if self._update_dialog:
            self._update_dialog.set_update_found(latest_version, html_url)

    def _on_up_to_date(self) -> None:
        """Routes up to date event to UpdateDialog UI."""
        if self._update_dialog:
            self._update_dialog.set_up_to_date()

    def _on_update_error(self, err_msg: str) -> None:
        """Routes error event to UpdateDialog UI."""
        logger.warning("Error al comprobar actualizaciones: %s", err_msg)
        if self._update_dialog:
            self._update_dialog.set_error(err_msg)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Pops up DropletMenu at cursor position when tray icon is clicked."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.menu:
                self.menu.exec(QCursor.pos())
