"""
Представление для отображения статуса принтера
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont

from .styles import Styles
from ..models import PrinterStatus, PrinterState
from ..services import StatusService


class StatusView(QWidget):
    """Представление статуса принтера"""

    navigate_back = pyqtSignal()

    def __init__(self, status_service: StatusService, parent=None):
        super().__init__(parent)
        self._status_service = status_service

        self._init_ui()

        # Подписываемся на обновления статуса
        self._status_service.add_status_changed_callback(self._on_status_changed)

        # Таймер для обновления интерфейса
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(1000)

    def _init_ui(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Заголовок
        header_layout = QHBoxLayout()

        back_btn = QPushButton("< Назад")
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(f"background-color: {Styles.TEXT_SECONDARY};")
        back_btn.clicked.connect(self.navigate_back.emit)
        header_layout.addWidget(back_btn)

        header_layout.addStretch()

        title_label = QLabel("СТАТУС ПРИНТЕРА")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        header_layout.addSpacing(100)

        main_layout.addLayout(header_layout)

        # Основной контент
        content_frame = QFrame()
        content_frame.setStyleSheet(Styles.get_card_style())
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(30)

        # Статус подключения
        status_group = QGroupBox("Состояние")
        status_layout = QVBoxLayout(status_group)

        # Индикатор онлайн/офлайн
        indicator_layout = QHBoxLayout()
        self._status_indicator = QLabel("●")
        self._status_indicator.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 40px;")
        indicator_layout.addWidget(self._status_indicator)

        self._status_text = QLabel("Проверка...")
        self._status_text.setStyleSheet("font-size: 24px; font-weight: bold;")
        indicator_layout.addWidget(self._status_text)

        indicator_layout.addStretch()
        status_layout.addLayout(indicator_layout)

        # Имя принтера
        self._printer_name_label = QLabel("Принтер: Не обнаружен")
        self._printer_name_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 16px;")
        status_layout.addWidget(self._printer_name_label)

        # Сообщение о статусе
        self._status_message_label = QLabel("")
        self._status_message_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 14px;")
        status_layout.addWidget(self._status_message_label)

        content_layout.addWidget(status_group)

        # Уровень тонера
        toner_group = QGroupBox("Уровень тонера")
        toner_layout = QVBoxLayout(toner_group)

        self._toner_bar = QProgressBar()
        self._toner_bar.setFixedHeight(40)
        self._toner_bar.setValue(0)
        self._toner_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 8px;
                background-color: #E0E0E0;
                text-align: center;
                font-size: 16px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {Styles.SUCCESS_COLOR};
                border-radius: 8px;
            }}
        """)
        toner_layout.addWidget(self._toner_bar)

        self._toner_label = QLabel("Неизвестно")
        self._toner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toner_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY};")
        toner_layout.addWidget(self._toner_label)

        content_layout.addWidget(toner_group)

        # Очередь печати
        queue_group = QGroupBox("Очередь печати")
        queue_layout = QVBoxLayout(queue_group)

        self._queue_label = QLabel("Заданий в очереди: 0")
        self._queue_label.setStyleSheet("font-size: 18px;")
        self._queue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        queue_layout.addWidget(self._queue_label)

        content_layout.addWidget(queue_group)

        # Возможности
        capabilities_group = QGroupBox("Возможности")
        capabilities_layout = QHBoxLayout(capabilities_group)

        self._print_capability = QLabel("✓ Печать")
        self._print_capability.setStyleSheet(f"color: {Styles.SUCCESS_COLOR}; font-size: 16px;")
        capabilities_layout.addWidget(self._print_capability)

        self._scan_capability = QLabel("✓ Сканирование")
        self._scan_capability.setStyleSheet(f"color: {Styles.SUCCESS_COLOR}; font-size: 16px;")
        capabilities_layout.addWidget(self._scan_capability)

        self._copy_capability = QLabel("✓ Копирование")
        self._copy_capability.setStyleSheet(f"color: {Styles.SUCCESS_COLOR}; font-size: 16px;")
        capabilities_layout.addWidget(self._copy_capability)

        capabilities_layout.addStretch()
        content_layout.addWidget(capabilities_group)

        # Последнее обновление
        self._last_update_label = QLabel("Последнее обновление: ---")
        self._last_update_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._last_update_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 12px;")
        content_layout.addWidget(self._last_update_label)

        content_layout.addStretch()
        main_layout.addWidget(content_frame, stretch=1)

        # Кнопка обновления
        refresh_btn = QPushButton("ОБНОВИТЬ СТАТУС")
        refresh_btn.setFixedHeight(60)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.PRIMARY_COLOR};
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
        """)
        refresh_btn.clicked.connect(self._refresh_status)
        main_layout.addWidget(refresh_btn)

    def _on_status_changed(self, status: PrinterStatus):
        """Callback при изменении статуса"""
        # Обновление будет происходить через таймер
        pass

    def _update_display(self):
        """Обновить отображение статуса"""
        status = self._status_service.get_current_status()

        # Обновляем индикатор
        if status.is_online:
            self._status_indicator.setStyleSheet(f"color: {Styles.SUCCESS_COLOR}; font-size: 40px;")
            self._status_text.setText("В сети")
            self._status_text.setStyleSheet(f"color: {Styles.SUCCESS_COLOR}; font-size: 24px; font-weight: bold;")
        else:
            self._status_indicator.setStyleSheet(f"color: {Styles.DANGER_COLOR}; font-size: 40px;")
            self._status_text.setText("Не в сети")
            self._status_text.setStyleSheet(f"color: {Styles.DANGER_COLOR}; font-size: 24px; font-weight: bold;")

        # Имя принтера
        if status.printer_name:
            self._printer_name_label.setText(f"Принтер: {status.printer_name}")
        else:
            self._printer_name_label.setText("Принтер: Не обнаружен")

        # Сообщение о статусе
        self._status_message_label.setText(status.status_message)

        # Уровень тонера
        if status.toner_level >= 0:
            self._toner_bar.setValue(status.toner_level)
            self._toner_label.setText(f"{status.toner_level}%")

            # Меняем цвет в зависимости от уровня
            if status.toner_level < 20:
                color = Styles.DANGER_COLOR
            elif status.toner_level < 50:
                color = Styles.WARNING_COLOR
            else:
                color = Styles.SUCCESS_COLOR

            self._toner_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 8px;
                    background-color: #E0E0E0;
                    text-align: center;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 8px;
                }}
            """)
        else:
            self._toner_bar.setValue(0)
            self._toner_label.setText("Неизвестно")

        # Очередь печати
        self._queue_label.setText(f"Заданий в очереди: {status.jobs_in_queue}")

        # Возможности
        self._scan_capability.setStyleSheet(
            f"color: {Styles.SUCCESS_COLOR if status.supports_scanning else Styles.TEXT_SECONDARY}; font-size: 16px;"
        )
        self._copy_capability.setStyleSheet(
            f"color: {Styles.SUCCESS_COLOR if status.supports_copying else Styles.TEXT_SECONDARY}; font-size: 16px;"
        )

        # Последнее обновление
        self._last_update_label.setText(
            f"Последнее обновление: {status.last_updated.strftime('%H:%M:%S')}"
        )

    def _refresh_status(self):
        """Принудительное обновление статуса"""
        self._status_service._update_status()
        self._update_display()

    def showEvent(self, event):
        """При показе страницы"""
        super().showEvent(event)
        self._update_display()

    def hideEvent(self, event):
        """При скрытии страницы"""
        super().hideEvent(event)
