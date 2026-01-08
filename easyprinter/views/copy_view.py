"""
Представление для копирования документов
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider,
    QFrame, QMessageBox, QProgressBar, QGroupBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage, QFont
from PIL import Image

from .styles import Styles
from ..models import ScanSettings, ScanResolution, ScanSource, PrintSettings
from ..services import ScannerService, PrinterService, ImageProcessingService


class CopyWorker(QThread):
    """Рабочий поток для копирования"""
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool, str)

    def __init__(self, scanner_service: ScannerService, printer_service: PrinterService,
                 scan_settings: ScanSettings, print_settings: PrintSettings, copies: int):
        super().__init__()
        self.scanner_service = scanner_service
        self.printer_service = printer_service
        self.scan_settings = scan_settings
        self.print_settings = print_settings
        self.copies = copies

    def run(self):
        try:
            # Шаг 1: Сканирование
            self.progress.emit("Сканирование документа...", 20)
            image = self.scanner_service.scan(self.scan_settings)

            if image is None:
                self.finished.emit(False, "Не удалось отсканировать документ")
                return

            # Шаг 2: Сохранение во временный файл
            self.progress.emit("Подготовка к печати...", 50)
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                image.save(tmp_path, 'PNG')

            try:
                # Шаг 3: Печать
                self.progress.emit("Печать копии...", 80)
                self.print_settings.copies = self.copies
                self.printer_service.print_file(tmp_path, self.print_settings)

                self.progress.emit("Копирование завершено", 100)
                self.finished.emit(True, f"Успешно создано копий: {self.copies}")

            finally:
                # Удаляем временный файл
                try:
                    os.unlink(tmp_path)
                except:
                    pass

        except Exception as e:
            self.finished.emit(False, str(e))


class CopyView(QWidget):
    """Представление для копирования"""

    navigate_back = pyqtSignal()

    def __init__(self, scanner_service: ScannerService, printer_service: PrinterService,
                 image_processing: ImageProcessingService, parent=None):
        super().__init__(parent)
        self._scanner_service = scanner_service
        self._printer_service = printer_service
        self._image_processing = image_processing
        self._copy_worker: Optional[CopyWorker] = None

        self._init_ui()

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

        title_label = QLabel("КОПИРОВАНИЕ")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        header_layout.addSpacing(100)

        main_layout.addLayout(header_layout)

        # Центральный контент
        content_frame = QFrame()
        content_frame.setStyleSheet(Styles.get_card_style())
        content_layout = QVBoxLayout(content_frame)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(30)

        # Иконка
        icon_label = QLabel("📋")
        icon_label.setStyleSheet("font-size: 80px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(icon_label)

        # Описание
        desc_label = QLabel("Положите документ на стекло сканера\nи нажмите кнопку 'Копировать'")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 16px;")
        content_layout.addWidget(desc_label)

        # Настройки копирования
        settings_group = QGroupBox("Настройки копирования")
        settings_layout = QVBoxLayout(settings_group)

        # Количество копий
        copies_layout = QHBoxLayout()
        copies_layout.addWidget(QLabel("Количество копий:"))
        self._copies_spin = QSpinBox()
        self._copies_spin.setRange(1, 99)
        self._copies_spin.setValue(1)
        self._copies_spin.setFixedWidth(100)
        copies_layout.addWidget(self._copies_spin)
        copies_layout.addStretch()
        settings_layout.addLayout(copies_layout)

        # Источник
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Источник:"))
        self._source_combo = QComboBox()
        self._source_combo.addItems(["Стекло сканера", "Автоподатчик (АПД)"])
        self._source_combo.setFixedWidth(200)
        source_layout.addWidget(self._source_combo)
        source_layout.addStretch()
        settings_layout.addLayout(source_layout)

        # Масштаб
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Масштаб:"))
        self._scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._scale_slider.setRange(25, 400)
        self._scale_slider.setValue(100)
        self._scale_slider.setFixedWidth(200)
        self._scale_slider.valueChanged.connect(self._on_scale_changed)
        scale_layout.addWidget(self._scale_slider)
        self._scale_label = QLabel("100%")
        self._scale_label.setFixedWidth(50)
        scale_layout.addWidget(self._scale_label)
        scale_layout.addStretch()
        settings_layout.addLayout(scale_layout)

        content_layout.addWidget(settings_group)

        # Прогресс
        self._progress_widget = QWidget()
        progress_layout = QVBoxLayout(self._progress_widget)
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(400)
        self._progress_bar.setFixedHeight(30)
        progress_layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("Копирование...")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self._progress_label)

        self._progress_widget.setVisible(False)
        content_layout.addWidget(self._progress_widget)

        main_layout.addWidget(content_frame, stretch=1)

        # Кнопка копирования
        self._copy_btn = QPushButton("КОПИРОВАТЬ")
        self._copy_btn.setFixedHeight(80)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.WARNING_COLOR};
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: #FB8C00;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
            }}
        """)
        self._copy_btn.clicked.connect(self._on_copy_clicked)
        main_layout.addWidget(self._copy_btn)

    def _on_scale_changed(self, value: int):
        """Обработчик изменения масштаба"""
        self._scale_label.setText(f"{value}%")

    def _on_copy_clicked(self):
        """Обработчик нажатия кнопки копирования"""
        # Настройки сканирования
        scan_settings = ScanSettings()
        scan_settings.resolution = ScanResolution.DPI_300
        sources = [ScanSource.FLATBED, ScanSource.ADF]
        scan_settings.source = sources[self._source_combo.currentIndex()]

        # Настройки печати
        print_settings = PrintSettings()
        print_settings.scale = self._scale_slider.value()
        print_settings.copies = self._copies_spin.value()

        # Показываем прогресс
        self._progress_widget.setVisible(True)
        self._progress_bar.setValue(0)
        self._copy_btn.setEnabled(False)

        # Запускаем копирование
        self._copy_worker = CopyWorker(
            self._scanner_service,
            self._printer_service,
            scan_settings,
            print_settings,
            self._copies_spin.value()
        )
        self._copy_worker.progress.connect(self._on_progress)
        self._copy_worker.finished.connect(self._on_finished)
        self._copy_worker.start()

    @pyqtSlot(str, int)
    def _on_progress(self, message: str, progress: int):
        """Обработчик прогресса"""
        self._progress_bar.setValue(progress)
        self._progress_label.setText(message)

    @pyqtSlot(bool, str)
    def _on_finished(self, success: bool, message: str):
        """Обработчик завершения"""
        self._copy_btn.setEnabled(True)
        self._progress_widget.setVisible(False)

        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.warning(self, "Ошибка", f"Ошибка копирования: {message}")
