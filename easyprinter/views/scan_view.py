"""
Представление для сканирования документов
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSlider,
    QFileDialog, QScrollArea, QFrame, QMessageBox,
    QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage, QFont
from PIL import Image
from datetime import datetime

from .styles import Styles
from ..models import ScanSettings, ScanResolution, ScanFormat, ScanSource
from ..services import ScannerService, ImageProcessingService, logger


class ScanWorker(QThread):
    """Рабочий поток для сканирования"""
    finished = pyqtSignal(object)  # Image or None
    progress = pyqtSignal(str, int)
    error = pyqtSignal(str)

    def __init__(self, scanner_service: ScannerService, settings: ScanSettings):
        super().__init__()
        self.scanner_service = scanner_service
        self.settings = settings

    def run(self):
        try:
            # Подключаем callback для прогресса
            def on_progress(event):
                self.progress.emit(event.message, event.progress)

            self.scanner_service.add_progress_callback(on_progress)

            image = self.scanner_service.scan(self.settings)
            self.finished.emit(image)
        except Exception as e:
            logger.exception(f"Ошибка сканирования: {e}")
            self.error.emit(str(e))
        finally:
            # Удаляем callback
            try:
                self.scanner_service._progress_callbacks.clear()
            except:
                pass


class ScanView(QWidget):
    """Представление для сканирования"""

    navigate_back = pyqtSignal()

    # DPI описания для подсказок
    DPI_DESCRIPTIONS = {
        150: "Быстро, небольшой размер файла (~0.5 МБ)",
        300: "Стандартное качество для документов (~2 МБ)",
        600: "Высокое качество для фото (~8 МБ)",
        1200: "Максимальное качество, большой файл (~30 МБ)"
    }

    def __init__(self, scanner_service: ScannerService, image_processing: ImageProcessingService, parent=None):
        super().__init__(parent)
        self._scanner_service = scanner_service
        self._image_processing = image_processing
        self._scanned_image: Optional[Image.Image] = None
        self._settings = ScanSettings()
        self._scan_worker: Optional[ScanWorker] = None

        self._init_ui()
        logger.info("Открыта страница сканирования")

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

        title_label = QLabel("СКАНИРОВАНИЕ")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        header_layout.addSpacing(100)

        main_layout.addLayout(header_layout)

        # Основной контент
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # Левая панель - предпросмотр
        preview_panel = self._create_preview_panel()
        content_layout.addWidget(preview_panel, stretch=2)

        # Правая панель - настройки
        settings_panel = self._create_settings_panel()
        content_layout.addWidget(settings_panel, stretch=1)

        main_layout.addLayout(content_layout)

        # Кнопки действий
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(20)

        self._scan_btn = QPushButton("СКАНИРОВАТЬ")
        self._scan_btn.setFixedHeight(80)
        self._scan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.PRIMARY_COLOR};
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
            }}
        """)
        self._scan_btn.clicked.connect(self._on_scan_clicked)
        actions_layout.addWidget(self._scan_btn)

        self._save_btn = QPushButton("СОХРАНИТЬ")
        self._save_btn.setFixedHeight(80)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.SUCCESS_COLOR};
                color: white;
                font-size: 20px;
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: #43A047;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
            }}
        """)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save_clicked)
        actions_layout.addWidget(self._save_btn)

        main_layout.addLayout(actions_layout)

    def _create_preview_panel(self) -> QFrame:
        """Создать панель предпросмотра"""
        frame = QFrame()
        frame.setStyleSheet(Styles.get_card_style())
        layout = QVBoxLayout(frame)

        # Заголовок
        title_label = QLabel("Предпросмотр скана")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Область предпросмотра
        preview_container = QFrame()
        preview_container.setStyleSheet("background-color: #F0F0F0; border-radius: 8px;")
        preview_layout = QVBoxLayout(preview_container)

        # Плейсхолдер
        self._placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(self._placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        placeholder_label = QLabel("Нажмите 'Сканировать' для начала")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 16px;")
        placeholder_layout.addWidget(placeholder_label)

        preview_layout.addWidget(self._placeholder_widget)

        # Прогресс сканирования
        self._progress_widget = QWidget()
        progress_layout = QVBoxLayout(self._progress_widget)
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(300)
        self._progress_bar.setFixedHeight(30)
        progress_layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("Сканирование...")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setStyleSheet("margin-top: 15px;")
        progress_layout.addWidget(self._progress_label)

        self._progress_widget.setVisible(False)
        preview_layout.addWidget(self._progress_widget)

        # Превью изображения
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumSize(400, 400)
        self._preview_label.setVisible(False)
        preview_layout.addWidget(self._preview_label)

        layout.addWidget(preview_container, stretch=1)

        return frame

    def _create_settings_panel(self) -> QScrollArea:
        """Создать панель настроек"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)

        # Настройки сканирования
        scan_group = QGroupBox("Настройки сканирования")
        scan_layout = QVBoxLayout(scan_group)

        # Источник
        scan_layout.addWidget(QLabel("Источник:"))
        self._source_combo = QComboBox()
        self._source_combo.addItems([
            "Стекло сканера",
            "Автоподатчик (АПД)"
        ])
        self._source_combo.currentIndexChanged.connect(self._update_settings)
        scan_layout.addWidget(self._source_combo)

        # Разрешение (DPI) с подсказкой
        dpi_label = QLabel("Качество (DPI):")
        scan_layout.addWidget(dpi_label)

        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems([
            "150 DPI - быстро",
            "300 DPI - стандарт",
            "600 DPI - высокое",
            "1200 DPI - максимум"
        ])
        self._resolution_combo.setCurrentIndex(1)
        self._resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        scan_layout.addWidget(self._resolution_combo)

        # Подсказка о размере файла
        self._dpi_hint_label = QLabel(self.DPI_DESCRIPTIONS[300])
        self._dpi_hint_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 11px; font-style: italic;")
        self._dpi_hint_label.setWordWrap(True)
        scan_layout.addWidget(self._dpi_hint_label)

        layout.addWidget(scan_group)

        # Настройки сохранения
        save_group = QGroupBox("Сохранение")
        save_layout = QVBoxLayout(save_group)

        # Формат файла
        save_layout.addWidget(QLabel("Формат файла:"))
        self._format_combo = QComboBox()
        self._format_combo.addItems([
            "PDF - документ",
            "JPEG - сжатое фото",
            "PNG - без потерь",
            "TIFF - архивный"
        ])
        self._format_combo.currentIndexChanged.connect(self._update_settings)
        save_layout.addWidget(self._format_combo)

        # Имя файла
        save_layout.addWidget(QLabel("Имя файла:"))
        self._filename_edit = QLineEdit()
        self._filename_edit.setText(f"Скан_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
        self._filename_edit.textChanged.connect(self._update_settings)
        save_layout.addWidget(self._filename_edit)

        # Папка сохранения
        save_layout.addWidget(QLabel("Папка для сохранения:"))
        folder_layout = QHBoxLayout()
        self._folder_edit = QLineEdit()
        self._folder_edit.setText(str(self._settings.output_folder))
        self._folder_edit.setReadOnly(True)
        folder_layout.addWidget(self._folder_edit)

        browse_btn = QPushButton("Обзор...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._on_browse_folder)
        folder_layout.addWidget(browse_btn)

        save_layout.addLayout(folder_layout)

        layout.addWidget(save_group)

        # Настройки изображения
        image_group = QGroupBox("Коррекция изображения")
        image_layout = QVBoxLayout(image_group)

        # Яркость
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Яркость:"))
        self._brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self._brightness_slider.setRange(-100, 100)
        self._brightness_slider.setValue(0)
        self._brightness_slider.valueChanged.connect(self._on_image_adjustment_changed)
        brightness_layout.addWidget(self._brightness_slider)
        self._brightness_label = QLabel("0")
        self._brightness_label.setFixedWidth(40)
        brightness_layout.addWidget(self._brightness_label)
        image_layout.addLayout(brightness_layout)

        # Контраст
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Контраст:"))
        self._contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self._contrast_slider.setRange(-100, 100)
        self._contrast_slider.setValue(0)
        self._contrast_slider.valueChanged.connect(self._on_image_adjustment_changed)
        contrast_layout.addWidget(self._contrast_slider)
        self._contrast_label = QLabel("0")
        self._contrast_label.setFixedWidth(40)
        contrast_layout.addWidget(self._contrast_label)
        image_layout.addLayout(contrast_layout)

        # Резкость
        sharpness_layout = QHBoxLayout()
        sharpness_layout.addWidget(QLabel("Резкость:"))
        self._sharpness_slider = QSlider(Qt.Orientation.Horizontal)
        self._sharpness_slider.setRange(0, 100)
        self._sharpness_slider.setValue(0)
        self._sharpness_slider.valueChanged.connect(self._on_image_adjustment_changed)
        sharpness_layout.addWidget(self._sharpness_slider)
        self._sharpness_label = QLabel("0")
        self._sharpness_label.setFixedWidth(40)
        sharpness_layout.addWidget(self._sharpness_label)
        image_layout.addLayout(sharpness_layout)

        # Кнопка сброса
        reset_btn = QPushButton("Сбросить настройки")
        reset_btn.setStyleSheet(f"background-color: {Styles.TEXT_SECONDARY};")
        reset_btn.clicked.connect(self._reset_image_settings)
        image_layout.addWidget(reset_btn)

        layout.addWidget(image_group)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _on_resolution_changed(self, index: int):
        """Обработчик изменения разрешения"""
        dpi_values = [150, 300, 600, 1200]
        dpi = dpi_values[index]
        self._dpi_hint_label.setText(self.DPI_DESCRIPTIONS[dpi])
        self._update_settings()

    def _update_settings(self):
        """Обновить настройки сканирования"""
        sources = [ScanSource.FLATBED, ScanSource.ADF]
        self._settings.source = sources[self._source_combo.currentIndex()]

        resolutions = [ScanResolution.DPI_150, ScanResolution.DPI_300, ScanResolution.DPI_600, ScanResolution.DPI_1200]
        self._settings.resolution = resolutions[self._resolution_combo.currentIndex()]

        formats = [ScanFormat.PDF, ScanFormat.JPEG, ScanFormat.PNG, ScanFormat.TIFF]
        self._settings.format = formats[self._format_combo.currentIndex()]

        self._settings.file_name = self._filename_edit.text()

    def _on_browse_folder(self):
        """Выбор папки для сохранения"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения сканов",
            self._settings.output_folder
        )
        if folder:
            self._settings.output_folder = folder
            self._folder_edit.setText(folder)
            logger.info(f"Выбрана папка для сохранения: {folder}")

    def _on_image_adjustment_changed(self):
        """Обработчик изменения настроек изображения"""
        self._brightness_label.setText(str(self._brightness_slider.value()))
        self._contrast_label.setText(str(self._contrast_slider.value()))
        self._sharpness_label.setText(str(self._sharpness_slider.value()))

        self._settings.image_adjustments.brightness = self._brightness_slider.value()
        self._settings.image_adjustments.contrast = self._contrast_slider.value()
        self._settings.image_adjustments.sharpness = self._sharpness_slider.value()

        # Обновляем предпросмотр если есть отсканированное изображение
        if self._scanned_image:
            self._update_preview()

    def _reset_image_settings(self):
        """Сбросить настройки изображения"""
        self._brightness_slider.setValue(0)
        self._contrast_slider.setValue(0)
        self._sharpness_slider.setValue(0)
        self._settings.image_adjustments.reset()

        if self._scanned_image:
            self._update_preview()

    def _on_scan_clicked(self):
        """Обработчик нажатия кнопки сканирования"""
        self._update_settings()
        logger.info(f"Начато сканирование: {self._settings.resolution.value} DPI, формат {self._settings.format.value}")

        # Показываем прогресс
        self._placeholder_widget.setVisible(False)
        self._preview_label.setVisible(False)
        self._progress_widget.setVisible(True)
        self._progress_bar.setValue(0)

        self._scan_btn.setEnabled(False)
        self._save_btn.setEnabled(False)

        # Запускаем сканирование в отдельном потоке
        self._scan_worker = ScanWorker(self._scanner_service, self._settings)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

    @pyqtSlot(str, int)
    def _on_scan_progress(self, message: str, progress: int):
        """Обработчик прогресса сканирования"""
        self._progress_bar.setValue(progress)
        self._progress_label.setText(message)

    @pyqtSlot(object)
    def _on_scan_finished(self, image):
        """Обработчик завершения сканирования"""
        self._scan_btn.setEnabled(True)
        self._progress_widget.setVisible(False)

        if image:
            self._scanned_image = image
            self._save_btn.setEnabled(True)
            self._update_preview()
            logger.info("Сканирование успешно завершено")
        else:
            self._placeholder_widget.setVisible(True)
            logger.warning("Сканирование не вернуло изображение")
            QMessageBox.warning(self, "Ошибка", "Не удалось получить изображение от сканера")

    @pyqtSlot(str)
    def _on_scan_error(self, error: str):
        """Обработчик ошибки сканирования"""
        self._scan_btn.setEnabled(True)
        self._progress_widget.setVisible(False)
        self._placeholder_widget.setVisible(True)
        logger.error(f"Ошибка сканирования: {error}")
        QMessageBox.warning(self, "Ошибка сканирования", error)

    def _update_preview(self):
        """Обновить предпросмотр"""
        if not self._scanned_image:
            return

        # Применяем настройки изображения
        image = self._scanned_image
        if self._settings.image_adjustments.has_changes:
            image = self._image_processing.apply_adjustments(image, self._settings.image_adjustments)

        # Конвертируем в QPixmap
        if image.mode == 'RGBA':
            data = image.tobytes('raw', 'RGBA')
            qimg = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888)
        else:
            image_rgb = image.convert('RGB')
            data = image_rgb.tobytes('raw', 'RGB')
            qimg = QImage(data, image_rgb.width, image_rgb.height, QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self._preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._preview_label.setPixmap(scaled)
        self._preview_label.setVisible(True)

    def _on_save_clicked(self):
        """Обработчик нажатия кнопки сохранения"""
        if not self._scanned_image:
            return

        self._update_settings()

        try:
            # Применяем настройки перед сохранением
            image_to_save = self._scanned_image
            if self._settings.image_adjustments.has_changes:
                image_to_save = self._image_processing.apply_adjustments(
                    self._scanned_image, self._settings.image_adjustments
                )

            output_path = self._scanner_service.save_scan(image_to_save, self._settings)
            logger.info(f"Скан сохранён: {output_path}")
            QMessageBox.information(
                self, "Успех",
                f"Скан сохранён:\n{output_path}"
            )

            # Генерируем новое имя для следующего скана
            self._filename_edit.setText(f"Скан_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

        except Exception as e:
            logger.exception(f"Ошибка сохранения скана: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить скан: {e}")
