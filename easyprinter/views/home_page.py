"""
Главная страница приложения
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .styles import Styles


class HomePage(QWidget):
    """Главная страница с навигацией"""

    # Сигналы навигации
    navigate_to_print = pyqtSignal()
    navigate_to_scan = pyqtSignal()
    navigate_to_copy = pyqtSignal()
    navigate_to_status = pyqtSignal()
    navigate_to_settings = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Заголовок
        title_label = QLabel("EasyPrinter")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(48)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {Styles.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        # Подзаголовок
        subtitle_label = QLabel("Управление принтером HP LaserJet M1536dnf")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 16px;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(40)

        # Сетка навигационных кнопок
        nav_grid = QGridLayout()
        nav_grid.setSpacing(20)

        # Кнопка Печать
        print_btn = self._create_nav_button(
            "ПЕЧАТЬ",
            Styles.PRIMARY_COLOR,
            self.navigate_to_print.emit
        )
        nav_grid.addWidget(print_btn, 0, 0)

        # Кнопка Сканирование
        scan_btn = self._create_nav_button(
            "СКАН",
            Styles.SUCCESS_COLOR,
            self.navigate_to_scan.emit
        )
        nav_grid.addWidget(scan_btn, 0, 1)

        # Кнопка Копирование
        copy_btn = self._create_nav_button(
            "КОПИЯ",
            Styles.WARNING_COLOR,
            self.navigate_to_copy.emit
        )
        nav_grid.addWidget(copy_btn, 1, 0)

        # Кнопка Статус
        status_btn = self._create_nav_button(
            "СТАТУС",
            Styles.PURPLE_COLOR,
            self.navigate_to_status.emit
        )
        nav_grid.addWidget(status_btn, 1, 1)

        # Центрируем сетку
        nav_container = QWidget()
        nav_container.setLayout(nav_grid)
        layout.addWidget(nav_container, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(20)

        # Кнопка Настройки (меньше по размеру, внизу)
        settings_btn = QPushButton("⚙ НАСТРОЙКИ")
        settings_btn.setFixedSize(200, 50)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.TEXT_SECONDARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #5a6268;
            }}
            QPushButton:pressed {{
                background-color: #495057;
            }}
        """)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self.navigate_to_settings.emit)
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def _create_nav_button(self, text: str, color: str, callback) -> QPushButton:
        """Создать навигационную кнопку"""
        btn = QPushButton(text)
        btn.setFixedSize(200, 160)
        btn.setStyleSheet(Styles.get_nav_button_style(color))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn
