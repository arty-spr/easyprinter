"""
Главное окно приложения EasyPrinter
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from .styles import Styles
from .home_page import HomePage
from .print_view import PrintView
from .scan_view import ScanView
from .copy_view import CopyView
from .status_view import StatusView
from .settings_view import SettingsView
from ..services import StatusService, PrinterService, ScannerService, ImageProcessingService
from ..models import PrinterStatus


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()

        # Инициализация сервисов
        self._image_processing = ImageProcessingService()
        self._status_service = StatusService()
        self._printer_service = PrinterService(self._status_service, self._image_processing)
        self._scanner_service = ScannerService(self._image_processing)

        # Подписываемся на обновления статуса
        self._status_service.add_status_changed_callback(self._on_status_changed)

        self._init_ui()

        # Запускаем мониторинг статуса
        self._status_service.start_monitoring()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("EasyPrinter - HP LaserJet M1536dnf")
        self.setMinimumSize(1100, 800)
        self.resize(1200, 850)

        # Устанавливаем стиль
        self.setStyleSheet(Styles.get_main_stylesheet())

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Стек страниц
        self._stack = QStackedWidget()

        # Создаём страницы
        self._home_page = HomePage()
        self._home_page.navigate_to_print.connect(lambda: self._show_page(1))
        self._home_page.navigate_to_scan.connect(lambda: self._show_page(2))
        self._home_page.navigate_to_copy.connect(lambda: self._show_page(3))
        self._home_page.navigate_to_status.connect(lambda: self._show_page(4))
        self._home_page.navigate_to_settings.connect(lambda: self._show_page(5))

        self._print_view = PrintView(self._printer_service, self._image_processing)
        self._print_view.navigate_back.connect(lambda: self._show_page(0))

        self._scan_view = ScanView(self._scanner_service, self._image_processing)
        self._scan_view.navigate_back.connect(lambda: self._show_page(0))

        self._copy_view = CopyView(self._scanner_service, self._printer_service, self._image_processing)
        self._copy_view.navigate_back.connect(lambda: self._show_page(0))

        self._status_view = StatusView(self._status_service)
        self._status_view.navigate_back.connect(lambda: self._show_page(0))

        self._settings_view = SettingsView()
        self._settings_view.navigate_back.connect(lambda: self._show_page(0))

        # Добавляем страницы в стек
        self._stack.addWidget(self._home_page)      # 0
        self._stack.addWidget(self._print_view)     # 1
        self._stack.addWidget(self._scan_view)      # 2
        self._stack.addWidget(self._copy_view)      # 3
        self._stack.addWidget(self._status_view)    # 4
        self._stack.addWidget(self._settings_view)  # 5

        main_layout.addWidget(self._stack)

        # Статусная строка
        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)

    def _create_status_bar(self) -> QFrame:
        """Создать статусную строку"""
        frame = QFrame()
        frame.setProperty("class", "statusbar")
        frame.setFixedHeight(50)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Styles.CARD_BACKGROUND};
                border-top: 1px solid #E0E0E0;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 5, 20, 5)

        # Индикатор статуса
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)

        self._status_indicator = QLabel("●")
        self._status_indicator.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 16px;")
        status_layout.addWidget(self._status_indicator)

        self._printer_name_label = QLabel("HP LaserJet M1536dnf")
        self._printer_name_label.setStyleSheet(f"color: {Styles.TEXT_PRIMARY}; font-size: 14px;")
        status_layout.addWidget(self._printer_name_label)

        layout.addLayout(status_layout)

        # Статус сообщение
        self._status_message_label = QLabel("Проверка подключения...")
        self._status_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_message_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(self._status_message_label, stretch=1)

        # Уровень тонера
        toner_layout = QHBoxLayout()
        toner_layout.setSpacing(10)

        toner_label = QLabel("Тонер:")
        toner_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 14px;")
        toner_layout.addWidget(toner_label)

        self._toner_bar = QProgressBar()
        self._toner_bar.setFixedSize(100, 20)
        self._toner_bar.setValue(0)
        self._toner_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 5px;
                background-color: #E0E0E0;
            }}
            QProgressBar::chunk {{
                background-color: {Styles.SUCCESS_COLOR};
                border-radius: 5px;
            }}
        """)
        toner_layout.addWidget(self._toner_bar)

        self._toner_percent_label = QLabel("--")
        self._toner_percent_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 14px;")
        toner_layout.addWidget(self._toner_percent_label)

        layout.addLayout(toner_layout)

        return frame

    def _show_page(self, index: int):
        """Показать страницу по индексу"""
        self._stack.setCurrentIndex(index)

    def _on_status_changed(self, status: PrinterStatus):
        """Обработчик изменения статуса принтера"""
        # Обновляем индикатор
        if status.is_online:
            self._status_indicator.setStyleSheet(f"color: {Styles.SUCCESS_COLOR}; font-size: 16px;")
        else:
            self._status_indicator.setStyleSheet(f"color: {Styles.DANGER_COLOR}; font-size: 16px;")

        # Имя принтера
        if status.printer_name:
            self._printer_name_label.setText(status.printer_name)
        else:
            self._printer_name_label.setText("Принтер не найден")

        # Сообщение
        self._status_message_label.setText(status.status_message)

        # Тонер
        if status.toner_level >= 0:
            self._toner_bar.setValue(status.toner_level)
            self._toner_percent_label.setText(f"{status.toner_level}%")

            # Цвет в зависимости от уровня
            if status.toner_level < 20:
                color = Styles.DANGER_COLOR
            elif status.toner_level < 50:
                color = Styles.WARNING_COLOR
            else:
                color = Styles.SUCCESS_COLOR

            self._toner_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 5px;
                    background-color: #E0E0E0;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 5px;
                }}
            """)
        else:
            self._toner_bar.setValue(0)
            self._toner_percent_label.setText("--")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Останавливаем мониторинг
        self._status_service.stop_monitoring()
        self._status_service.dispose()
        self._scanner_service.dispose()

        super().closeEvent(event)
