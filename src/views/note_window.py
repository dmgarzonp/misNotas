"""View layer for Mis Apuntes application.

Implements compact post-it NoteWindow widget with macOS Sequoia & GNOME aesthetics:
DropletMenu with rounded drop arrow pointer, GNOME symbolic icons,
font family selector, image insertion via QFileDialog, and PDF export.
"""

import os
import tempfile
from typing import Dict, Optional
from PyQt6.QtCore import QEvent, QMimeData, QPoint, QRectF, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QCursor,
    QDesktopServices,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QIcon,
    QImage,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QTextCharFormat,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizeGrip,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from src.services.link_preview_service import LinkPreviewService
from src.views.sidebar import SidebarWidget
from src.views.styles import (
    PASTEL_THEMES,
    PastelTheme,
    get_gnome_icon,
    get_theme,
    get_window_qss,
)


class DropletMenu(QMenu):
    """QMenu subclass painting a rounded drop tail pointer arrow at top of popup box."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)

    def paintEvent(self, event) -> None:
        """Paints rounded menu container with top droplet arrow pointer."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(2, 10, -2, -2)
        width = rect.width()

        # Build rounded rectangle with top droplet arrow tail path
        path = QPainterPath()
        path.moveTo(rect.left() + 14, rect.top())

        # Top Droplet Arrow Tail
        arrow_center_x = width / 2.0
        path.lineTo(arrow_center_x - 8, rect.top())
        path.lineTo(arrow_center_x, rect.top() - 8)
        path.lineTo(arrow_center_x + 8, rect.top())

        path.lineTo(rect.right() - 14, rect.top())
        path.arcTo(rect.right() - 28, rect.top(), 28, 28, 90, -90)
        path.lineTo(rect.right(), rect.bottom() - 14)
        path.arcTo(rect.right() - 28, rect.bottom() - 28, 28, 28, 0, -90)
        path.lineTo(rect.left() + 14, rect.bottom())
        path.arcTo(rect.left(), rect.bottom() - 28, 28, 28, 270, -90)
        path.lineTo(rect.left(), rect.top() + 14)
        path.arcTo(rect.left(), rect.top(), 28, 28, 180, -90)
        path.closeSubpath()

        # Paint Menu Background & Border
        bg_color = QColor(self.palette().window().color())
        border_color = QColor(self.palette().mid().color())

        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)
        painter.end()

        super().paintEvent(event)


class TexturedTextEdit(QTextEdit):
    """QTextEdit subclass supporting notebook backgrounds and Drag & Drop of images/files."""

    file_dropped = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.background_style: str = "blank"  # "blank", "ruled", "grid"
        self.line_color: str = "rgba(0, 0, 0, 0.1)"
        self.setAcceptDrops(True)

    def set_texture_style(self, style_name: str, line_color: str) -> None:
        """Sets background texture mode and triggers repaint."""
        self.background_style = style_name
        self.line_color = line_color
        vp = self.viewport()
        if vp:
            vp.update()

    def mouseReleaseEvent(self, event: Optional[QMouseEvent]) -> None:
        """Opens external URLs (such as YouTube videos or web links) in default browser when clicked."""
        if event and event.button() == Qt.MouseButton.LeftButton:
            anchor = self.anchorAt(event.pos())
            if anchor and anchor.startswith(("http://", "https://")):
                QDesktopServices.openUrl(QUrl(anchor))
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: Optional[QDragEnterEvent]) -> None:
        """Accepts drag enter events containing URLs or image files."""
        if event:
            mime = event.mimeData()
            if mime and (mime.hasUrls() or mime.hasText()):
                event.acceptProposedAction()
                return
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: Optional[QDragMoveEvent]) -> None:
        """Accepts drag move events."""
        if event:
            mime = event.mimeData()
            if mime and (mime.hasUrls() or mime.hasText()):
                event.acceptProposedAction()
                return
            super().dragMoveEvent(event)

    def insertFromMimeData(self, source: Optional[QMimeData]) -> None:
        """Handles pasting images directly from system clipboard (e.g. Ctrl+V / screenshots)."""
        if not source:
            return

        if source.hasImage():
            image_data = source.imageData()
            if image_data is not None:
                image = (
                    image_data if isinstance(image_data, QImage) else QImage(image_data)
                )
                if not image.isNull():
                    with tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    ) as tmp:
                        tmp_path = tmp.name
                    if image.save(tmp_path, "PNG"):
                        self.file_dropped.emit(tmp_path)
                        return

        if source.hasUrls():
            for url in source.urls():
                local_path = url.toLocalFile()
                if local_path and os.path.exists(local_path):
                    ext = os.path.splitext(local_path)[1].lower()
                    if ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"):
                        self.file_dropped.emit(local_path)
                        return

        if source.hasText():
            text = source.text().strip()
            if LinkPreviewService.is_youtube_url(text):
                card_html = LinkPreviewService.generate_youtube_card_html(text)
                if card_html:
                    cursor = self.textCursor()
                    cursor.insertHtml(card_html)
                    return
            elif text.startswith(("http://", "https://")) and not (
                " " in text or "\n" in text
            ):
                card_html = LinkPreviewService.generate_web_card_html(text)
                cursor = self.textCursor()
                cursor.insertHtml(card_html)
                return

        super().insertFromMimeData(source)

    def dropEvent(self, event: Optional[QDropEvent]) -> None:
        """Handles drop event for image files or text and renders image in text document."""
        if not event:
            return
        mime = event.mimeData()
        if mime and mime.hasUrls():
            cursor = self.textCursor()
            for url in mime.urls():
                local_path = url.toLocalFile()
                if local_path and os.path.exists(local_path):
                    ext = os.path.splitext(local_path)[1].lower()
                    if ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"):
                        self.file_dropped.emit(local_path)
                    else:
                        cursor.insertText(f"📎 {os.path.basename(local_path)}\n")
            event.acceptProposedAction()
            vp = self.viewport()
            if vp:
                vp.update()
        else:
            super().dropEvent(event)

    def paintEvent(self, event) -> None:
        """Paints notebook background lines or grid if enabled."""
        vp = self.viewport()
        if vp and self.background_style in ("ruled", "grid"):
            painter = QPainter(vp)
            pen = QPen(QColor(self.line_color))
            pen.setWidth(1)
            painter.setPen(pen)

            line_height = 24
            offset_y = 10
            width = vp.width()
            height = vp.height()

            for y in range(offset_y, height, line_height):
                painter.drawLine(0, y, width, y)

            if self.background_style == "grid":
                for x in range(line_height, width, line_height):
                    painter.drawLine(x, 0, x, height)

            painter.end()

        super().paintEvent(event)


class NoteWindow(QWidget):
    """Compact Post-it NoteWindow with DropletMenu, GNOME symbolic icons, and rich formatting."""

    # UI Interaction Signals
    title_changed = pyqtSignal(str)
    content_changed = pyqtSignal(str)
    theme_changed = pyqtSignal(str)
    background_style_changed = pyqtSignal(str)
    new_note_requested = pyqtSignal()
    delete_note_requested = pyqtSignal()
    pin_requested = pyqtSignal()
    lock_requested = pyqtSignal()
    toggle_sidebar_requested = pyqtSignal()
    close_requested = pyqtSignal()
    image_requested = pyqtSignal()
    export_pdf_requested = pyqtSignal()
    window_resized = pyqtSignal(int, int)
    window_moved = pyqtSignal(int, int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.drag_position: QPoint = QPoint()
        self.current_theme_name: str = "honey"
        self.is_pinned: bool = False
        self.is_locked: bool = False

        # Auto-hide status timer
        self.status_hide_timer = QTimer(self)
        self.status_hide_timer.setSingleShot(True)
        self.status_hide_timer.setInterval(1500)
        self.status_hide_timer.timeout.connect(self._hide_status_badge)

        self._setup_window_flags()
        self._init_ui()
        self._apply_theme(self.current_theme_name)

    def _setup_window_flags(self) -> None:
        """Sets frameless window hint and translucent background attribute for compact post-it size."""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setMinimumSize(240, 200)
        self.resize(300, 280)

    def _init_ui(self) -> None:
        """Constructs UI hierarchy with shadow container and inner layout."""
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(14, 14, 14, 14)

        self.container = QWidget(self)
        self.container.setObjectName("ContainerWidget")
        self.container.setMouseTracking(True)

        self.shadow_effect = QGraphicsDropShadowEffect(self.container)
        self.shadow_effect.setBlurRadius(28.0)
        self.shadow_effect.setOffset(0, 6)
        self.shadow_effect.setColor(QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(self.shadow_effect)

        self.main_h_layout = QHBoxLayout(self.container)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        # Sidebar Widget (Collapsible)
        self.sidebar = SidebarWidget(self.container)
        self.sidebar.hide()
        self.main_h_layout.addWidget(self.sidebar)

        # Main Note Area
        self.note_area = QWidget(self.container)
        self.note_area.setMouseTracking(True)
        self.inner_layout = QVBoxLayout(self.note_area)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(0)

        # Build Components (Pure Canvas)
        self._build_title_input()
        self._build_content_editor()
        self._build_footer()

        self.main_h_layout.addWidget(self.note_area, 1)
        self.outer_layout.addWidget(self.container)

    def _build_title_input(self) -> None:
        """Creates line edit widget for note title with placeholder 'Mis Apuntes'."""
        self.title_input = QLineEdit(self.note_area)
        self.title_input.setObjectName("TitleInput")
        self.title_input.setPlaceholderText("Mis Apuntes")
        self.title_input.textChanged.connect(self.title_changed.emit)
        self.inner_layout.addWidget(self.title_input)

    def _build_content_editor(self) -> None:
        """Creates text edit widget for note content with DropletMenu context menu."""
        self.content_edit = TexturedTextEdit(self.note_area)
        self.content_edit.setObjectName("ContentEdit")
        self.content_edit.setPlaceholderText("Escribe tus apuntes aquí...")
        self.content_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.content_edit.customContextMenuRequested.connect(self._show_context_menu)
        self.content_edit.textChanged.connect(self._on_content_text_changed)
        self.inner_layout.addWidget(self.content_edit, 1)

    def _build_footer(self) -> None:
        """Creates bottom footer with hand cursor indicator for window dragging and QSizeGrip."""
        self.footer = QWidget(self.note_area)
        self.footer.setMouseTracking(True)
        self.footer.setCursor(Qt.CursorShape.OpenHandCursor)
        self.footer.setToolTip("Arrastrar para mover ventana por el escritorio")

        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(12, 2, 6, 4)

        self.drag_hint = QLabel("✋ Arrastrar ventana", self.footer)
        theme = get_theme(self.current_theme_name)
        self.drag_hint.setStyleSheet(
            f"color: {theme.muted_text}; font-size: 10px; opacity: 0.6;"
        )

        self.status_badge = QLabel("Guardado", self.footer)
        self.status_badge.setObjectName("StatusBadge")
        self.status_badge.hide()

        # Window Size Grip for Resizing Frameless Window
        self.size_grip = QSizeGrip(self.footer)
        self.size_grip.setCursor(Qt.CursorShape.SizeFDiagCursor)

        footer_layout.addWidget(self.drag_hint)
        footer_layout.addStretch()
        footer_layout.addWidget(self.status_badge)
        footer_layout.addWidget(
            self.size_grip,
            0,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
        )
        self.inner_layout.addWidget(self.footer)

    def _create_color_swatches_widget(self, parent_menu: QMenu) -> QWidgetAction:
        """Creates custom QWidgetAction displaying 4 circular color swatches inside context menu."""
        action = QWidgetAction(parent_menu)
        swatch_widget = QWidget(parent_menu)
        layout = QHBoxLayout(swatch_widget)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        for theme_key, theme_obj in PASTEL_THEMES.items():
            btn = QPushButton(swatch_widget)
            btn.setFixedSize(22, 22)
            btn.setToolTip(theme_obj.display_name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            is_active = theme_key == self.current_theme_name
            border_col = theme_obj.swatch_darker if is_active else "transparent"
            btn.setStyleSheet(
                f"background-color: {theme_obj.swatch_color}; border-radius: 11px; border: 2px solid {border_col};"
            )
            btn.clicked.connect(
                lambda checked, name=theme_key, m=parent_menu: (
                    self._on_swatch_in_menu_clicked(name, m)
                )
            )
            layout.addWidget(btn)

        action.setDefaultWidget(swatch_widget)
        return action

    def _on_swatch_in_menu_clicked(self, theme_name: str, menu: QMenu) -> None:
        """Handles color swatch click inside context menu."""
        menu.close()
        self._on_theme_selected(theme_name)

    def _show_context_menu(self, pos: QPoint) -> None:
        """Displays DropletMenu using native GNOME symbolic icons."""
        menu = DropletMenu(self.content_edit)

        # 1. Nueva Nota (Ctrl+A)
        new_icon = get_gnome_icon("document-new-symbolic")
        menu.addAction(new_icon, "Nueva Nota (Ctrl+A)", self.new_note_requested.emit)
        menu.addSeparator()

        # 2. Pastel Theme Selection Submenu
        theme_icon = get_gnome_icon("preferences-desktop-theme-symbolic")
        theme_menu = menu.addMenu(theme_icon, "Tema de Color")
        if theme_menu:
            swatch_action = self._create_color_swatches_widget(theme_menu)
            theme_menu.addAction(swatch_action)

        # 3. 4-Level Typography Hierarchy Submenu
        fmt_icon = get_gnome_icon("format-text-large-symbolic")
        fmt_menu = menu.addMenu(fmt_icon, "Jerarquía de Texto")
        if fmt_menu:
            fmt_menu.addAction(
                "Título (H1)", lambda: self._apply_heading_format(20, True)
            )
            fmt_menu.addAction(
                "Encabezado (H2)", lambda: self._apply_heading_format(16, True)
            )
            fmt_menu.addAction(
                "Subencabezado (H3)", lambda: self._apply_heading_format(14, True)
            )
            fmt_menu.addAction(
                "Cuerpo (Normal)", lambda: self._apply_heading_format(13, False)
            )

        # 4. Font Family Selector Submenu
        font_icon = get_gnome_icon("font-x-generic-symbolic")
        font_menu = menu.addMenu(font_icon, "Fuente Tipográfica")
        if font_menu:
            font_menu.addAction(
                "Inter (Sans-serif)", lambda: self._apply_font_family("Inter")
            )
            font_menu.addAction(
                "SF Pro Text (Apple)", lambda: self._apply_font_family("SF Pro Text")
            )
            font_menu.addAction(
                "Roboto (Ubuntu)", lambda: self._apply_font_family("Roboto")
            )
            font_menu.addAction(
                "✍️ Manuscrita (Caveat)",
                lambda: self._apply_font_family(
                    "Caveat, Dancing Script, Segoe Script, Comic Sans MS, cursive"
                ),
            )
            font_menu.addAction(
                "Fira Code (Código)", lambda: self._apply_font_family("Fira Code")
            )
            font_menu.addAction(
                "Georgia (Serif)", lambda: self._apply_font_family("Georgia")
            )

        menu.addSeparator()
        # 5. Rich Elements & Media
        img_icon = get_gnome_icon("image-x-generic-symbolic")
        video_icon = get_gnome_icon("video-x-generic-symbolic")
        menu.addAction(img_icon, "Insertar Imagen...", self.image_requested.emit)
        menu.addAction(
            video_icon,
            "🎬 Insertar Tarjeta Video / Enlace...",
            self.insert_link_preview_dialog,
        )
        menu.addAction("☑ Insertar Checklist", self.insert_checklist)
        menu.addAction("📊 Insertar Tabla 2x2", self.insert_table)

        bg_icon = get_gnome_icon("document-page-setup-symbolic")
        bg_menu = menu.addMenu(bg_icon, "Fondo de Nota")
        if bg_menu:
            bg_menu.addAction(
                "Plano Pastel", lambda: self.set_background_texture("blank")
            )
            bg_menu.addAction(
                "Renglones de Cuaderno", lambda: self.set_background_texture("ruled")
            )
            bg_menu.addAction("Cuadrícula", lambda: self.set_background_texture("grid"))

        menu.addSeparator()
        pin_icon = get_gnome_icon("pin-symbolic")
        pin_text = "Desfijar Nota" if self.is_pinned else "Fijar Nota"
        menu.addAction(pin_icon, pin_text, self.pin_requested.emit)

        lock_icon = get_gnome_icon("system-lock-screen-symbolic")
        lock_text = "Quitar Protección" if self.is_locked else "Proteger con Contraseña"
        menu.addAction(lock_icon, lock_text, self.lock_requested.emit)

        pdf_icon = get_gnome_icon("document-save-as-symbolic")
        menu.addAction(pdf_icon, "Exportar a PDF...", self.export_pdf_requested.emit)

        delete_icon = get_gnome_icon("user-trash-symbolic")
        menu.addAction(delete_icon, "Eliminar Nota", self.delete_note_requested.emit)

        # Exit / Close Option
        menu.addSeparator()
        exit_icon = get_gnome_icon("application-exit-symbolic")
        menu.addAction(exit_icon, "Cerrar / Salir", self.close_requested.emit)

        menu.exec(self.content_edit.mapToGlobal(pos))

    def _apply_font_family(self, font_family: str) -> None:
        """Applies font family to text selection or cursor."""
        cursor = self.content_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontFamily(font_family)
        cursor.mergeCharFormat(fmt)
        self.content_edit.mergeCurrentCharFormat(fmt)

    def insert_image_html(self, file_url: str) -> None:
        """Inserts an image HTML element into the content editor."""
        cursor = self.content_edit.textCursor()
        img_html = (
            f'<br><img src="{file_url}" width="260" style="border-radius: 8px;"><br>'
        )
        cursor.insertHtml(img_html)
        vp = self.content_edit.viewport()
        if vp:
            vp.update()

    def insert_link_preview_dialog(self) -> None:
        """Prompts for a URL and inserts a YouTube video card or web preview link."""
        url, ok = QInputDialog.getText(
            self,
            "Insertar Enlace / Video YouTube",
            "Ingresa la URL del video de YouTube o sitio web:",
        )
        if ok and url.strip():
            clean_url = url.strip()
            if LinkPreviewService.is_youtube_url(clean_url):
                card_html = LinkPreviewService.generate_youtube_card_html(clean_url)
            else:
                card_html = LinkPreviewService.generate_web_card_html(clean_url)

            if card_html:
                cursor = self.content_edit.textCursor()
                cursor.insertHtml(card_html)
                vp = self.content_edit.viewport()
                if vp:
                    vp.update()

    def _on_theme_selected(self, theme_name: str) -> None:
        """Handles theme selection from context menu."""
        if theme_name != self.current_theme_name:
            self._apply_theme(theme_name)
            self.theme_changed.emit(theme_name)

    def _apply_heading_format(self, size: int, is_bold: bool) -> None:
        """Applies typography formatting to current text selection or line."""
        cursor = self.content_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(size))
        fmt.setFontWeight(QFont.Weight.Bold if is_bold else QFont.Weight.Normal)
        cursor.mergeCharFormat(fmt)
        self.content_edit.mergeCurrentCharFormat(fmt)

    def insert_checklist(self) -> None:
        """Inserts an interactive checklist item at current cursor position."""
        cursor = self.content_edit.textCursor()
        cursor.insertText("☐ ")
        self.content_edit.setTextCursor(cursor)

    def insert_table(self) -> None:
        """Inserts a clean 2x2 HTML table into the text editor."""
        cursor = self.content_edit.textCursor()
        table_html = """
        <table border="1" cellspacing="0" cellpadding="4" style="border-collapse: collapse; border-color: rgba(0,0,0,0.2);">
            <tr><td><b>Columna 1</b></td><td><b>Columna 2</b></td></tr>
            <tr><td>Dato 1</td><td>Dato 2</td></tr>
        </table>
        <p></p>
        """
        cursor.insertHtml(table_html)

    def set_background_texture(self, texture_style: str) -> None:
        """Changes the background texture style (blank, ruled, grid)."""
        theme = get_theme(self.current_theme_name)
        self.content_edit.set_texture_style(texture_style, theme.line_color)
        self.background_style_changed.emit(texture_style)

    def _on_content_text_changed(self) -> None:
        """Emits content_changed signal when text changes."""
        text = self.content_edit.toPlainText()
        self.content_changed.emit(text)

    def _apply_theme(self, theme_name: str) -> None:
        """Applies QSS stylesheet corresponding to selected theme."""
        self.current_theme_name = theme_name
        theme = get_theme(theme_name)
        self.setStyleSheet(get_window_qss(theme))

        if hasattr(self, "content_edit") and self.content_edit:
            self.content_edit.line_color = theme.line_color
            vp = self.content_edit.viewport()
            if vp:
                vp.update()

        if hasattr(self, "drag_hint") and self.drag_hint:
            self.drag_hint.setStyleSheet(
                f"color: {theme.muted_text}; font-size: 10px; opacity: 0.6;"
            )

    # Native Window Dragging Implementation (Wayland & X11)
    def mousePressEvent(self, event: Optional[QMouseEvent]) -> None:
        """Captures mouse press and invokes Qt6 native window startSystemMove."""
        if event and event.button() == Qt.MouseButton.LeftButton:
            win = self.windowHandle()
            if win:
                win.startSystemMove()
                event.accept()
                return

            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: Optional[QMouseEvent]) -> None:
        """Moves window when dragging mouse (fallback)."""
        if (
            event
            and event.buttons() == Qt.MouseButton.LeftButton
            and not self.drag_position.isNull()
        ):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: Optional[QMouseEvent]) -> None:
        """Resets drag position on mouse release."""
        self.drag_position = QPoint()

    def resizeEvent(self, event) -> None:
        """Emits window_resized signal when user resizes the window."""
        super().resizeEvent(event)
        size = self.size()
        self.window_resized.emit(size.width(), size.height())

    def moveEvent(self, event) -> None:
        """Emits window_moved signal when user moves or drags the window on the desktop."""
        super().moveEvent(event)
        pos = self.pos()
        self.window_moved.emit(pos.x(), pos.y())

    # Public View API
    def set_note_data(
        self,
        title: str,
        content: str,
        content_html: str = "",
        theme_name: str = "honey",
        pinned: bool = False,
        is_locked: bool = False,
        background_style: str = "blank",
        width: int = 300,
        height: int = 280,
        pos_x: int = 100,
        pos_y: int = 100,
    ) -> None:
        """Populates UI controls with note model data without emitting signals."""
        self.title_input.blockSignals(True)
        self.content_edit.blockSignals(True)

        self.title_input.setText(title)
        if content_html.strip():
            self.content_edit.setHtml(content_html)
        else:
            self.content_edit.setPlainText(content)

        self.is_pinned = pinned
        self.is_locked = is_locked

        self.title_input.blockSignals(False)
        self.content_edit.blockSignals(False)

        if width >= 200 and height >= 150:
            self.resize(width, height)

        if pos_x >= 0 and pos_y >= 0:
            self.move(pos_x, pos_y)

        self.set_background_texture(background_style)
        self._apply_theme(theme_name)

    def set_status_text(self, text: str) -> None:
        """Displays status badge while editing and schedules auto-hiding when saved."""
        self.status_hide_timer.stop()
        self.status_badge.setText(text)
        self.status_badge.show()

        if text.lower() == "guardado":
            self.status_hide_timer.start()

    def _hide_status_badge(self) -> None:
        """Hides status badge after save inactivity timeout."""
        self.status_badge.hide()

    def get_content_html(self) -> str:
        """Returns the HTML representation of current text editor content."""
        return self.content_edit.toHtml()
