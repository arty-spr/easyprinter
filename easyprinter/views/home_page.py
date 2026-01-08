"""
Главная страница приложения с поддержкой drag-and-drop
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from .styles import Styles


class DropZone(QFrame):
    """Зона для перетаскивания файлов"""

    file_dropped = pyqtSignal(str)

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._is_drag_over = False
        self._update_style()
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 80px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("Перетащите файл сюда\nдля быстрой печати")
        text_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_LARGE}px;
            color: {Styles.TEXT_SECONDARY};
            background: transparent;
        """)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        hint_label = QLabel("PDF, Word, изображения")
        hint_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_NORMAL}px;
            color: {Styles.TEXT_SECONDARY};
            background: transparent;
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

    def _update_style(self):
        self.setStyleSheet(Styles.get_drop_zone_style(self._is_drag_over))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self._is_drag_over = True
                    self._update_style()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._is_drag_over = False
        self._update_style()

    def dropEvent(self, event: QDropEvent):
        self._is_drag_over = False
        self._update_style()
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self.file_dropped.emit(file_path)
                    return
        event.ignore()


class HomePage(QWidget):
    """Главная страница с навигацией"""

    navigate_to_print = pyqtSignal()
    navigate_to_scan = pyqtSignal()
    navigate_to_copy = pyqtSignal()
    navigate_to_status = pyqtSignal()
    navigate_to_settings = pyqtSignal()
    quick_print_file = pyqtSignal(str)  # Новый сигнал

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 30)

        # Заголовок
        title_label = QLabel("EasyPrinter")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(Styles.FONT_SIZE_TITLE + 12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {Styles.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        subtitle_label = QLabel("Простая печать и сканирование")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: {Styles.FONT_SIZE_LARGE}px;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # Зона перетаскивания
        drop_zone = DropZone()
        drop_zone.setFixedSize(500, 200)
        drop_zone.file_dropped.connect(self.quick_print_file.emit)
        layout.addWidget(drop_zone, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(30)

        # Навигационные кнопки
        nav_grid = QGridLayout()
        nav_grid.setSpacing(25)

        print_btn = self._create_nav_button("🖨️\nПЕЧАТЬ", Styles.PRIMARY_COLOR, self.navigate_to_print.emit)
        nav_grid.addWidget(print_btn, 0, 0)

        scan_btn = self._create_nav_button("📷\nСКАН", Styles.SUCCESS_COLOR, self.navigate_to_scan.emit)
        nav_grid.addWidget(scan_btn, 0, 1)

        copy_btn = self._create_nav_button("📋\nКОПИЯ", Styles.WARNING_COLOR, self.navigate_to_copy.emit)
        nav_grid.addWidget(copy_btn, 1, 0)

        status_btn = self._create_nav_button("📊\nСТАТУС", Styles.PURPLE_COLOR, self.navigate_to_status.emit)
        nav_grid.addWidget(status_btn, 1, 1)

        nav_container = QWidget()
        nav_container.setLayout(nav_grid)
        layout.addWidget(nav_container, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(20)

        # Кнопка настроек
        settings_btn = QPushButton("⚙️  Настройки")
        settings_btn.setFixedSize(250, 70)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.TEXT_SECONDARY};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #5a6268; }}
        """)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self.navigate_to_settings.emit)
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def _create_nav_button(self, text: str, color: str, callback) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(220, 180)
        btn.setStyleSheet(Styles.get_nav_button_style(color))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn
