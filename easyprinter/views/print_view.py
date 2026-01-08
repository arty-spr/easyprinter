"""
Представление для печати документов
"""

import os
import tempfile
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSlider,
    QCheckBox, QFileDialog, QScrollArea, QFrame, QMessageBox,
    QSizePolicy, QGroupBox, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage, QFont, QTextDocument
from PIL import Image
import fitz  # PyMuPDF for PDF preview

from .styles import Styles
from ..models import (
    PrintSettings, PaperSize, PaperSource, PrintQuality,
    DuplexMode, PageOrientation, ImageAdjustments
)
from ..services import PrinterService, ImageProcessingService, logger

# Попытка импорта python-docx для поддержки Word документов
try:
    from docx import Document as DocxDocument
    from docx.shared import Inches
    DOCX_SUPPORTED = True
except ImportError:
    DOCX_SUPPORTED = False
    logger.warning("python-docx не установлен, предпросмотр DOCX недоступен")


class PrintWorker(QThread):
    """Рабочий поток для печати"""
    finished = pyqtSignal(bool, str)

    def __init__(self, printer_service: PrinterService, file_path: str, settings: PrintSettings):
        super().__init__()
        self.printer_service = printer_service
        self.file_path = file_path
        self.settings = settings

    def run(self):
        try:
            self.printer_service.print_file(self.file_path, self.settings)
            self.finished.emit(True, "Печать успешно отправлена")
        except Exception as e:
            logger.exception(f"Ошибка печати: {e}")
            self.finished.emit(False, str(e))


class PrintView(QWidget):
    """Представление для печати"""

    navigate_back = pyqtSignal()

    def __init__(self, printer_service: PrinterService, image_processing: ImageProcessingService, parent=None):
        super().__init__(parent)
        self._printer_service = printer_service
        self._image_processing = image_processing
        self._current_file: Optional[str] = None
        self._pdf_document = None
        self._current_page = 0
        self._total_pages = 1
        self._original_image: Optional[Image.Image] = None
        self._settings = PrintSettings()
        self._print_worker: Optional[PrintWorker] = None
        self._docx_text: Optional[str] = None

        self._init_ui()
        logger.info("Открыта страница печати")

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

        title_label = QLabel("ПЕЧАТЬ")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        header_layout.addSpacing(100)  # Для симметрии

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

        # Кнопка печати
        self._print_btn = QPushButton("ПЕЧАТЬ")
        self._print_btn.setFixedHeight(80)
        self._print_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.SUCCESS_COLOR};
                color: white;
                font-size: 24px;
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
        self._print_btn.setEnabled(False)
        self._print_btn.clicked.connect(self._on_print_clicked)
        main_layout.addWidget(self._print_btn)

    def _create_preview_panel(self) -> QFrame:
        """Создать панель предпросмотра"""
        frame = QFrame()
        frame.setStyleSheet(Styles.get_card_style())
        layout = QVBoxLayout(frame)

        # Выбор файла
        file_layout = QHBoxLayout()

        self._file_path_edit = QLineEdit()
        self._file_path_edit.setPlaceholderText("Выберите файл для печати...")
        self._file_path_edit.setReadOnly(True)
        file_layout.addWidget(self._file_path_edit)

        browse_btn = QPushButton("Обзор...")
        browse_btn.setFixedWidth(120)
        browse_btn.clicked.connect(self._on_browse_clicked)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        # Область предпросмотра
        preview_container = QFrame()
        preview_container.setStyleSheet("background-color: #F0F0F0; border-radius: 8px;")
        preview_layout = QVBoxLayout(preview_container)

        # Label для изображений/PDF
        self._preview_label = QLabel("Здесь будет предпросмотр документа")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 16px;")
        self._preview_label.setMinimumSize(400, 400)
        self._preview_label.setScaledContents(False)
        preview_layout.addWidget(self._preview_label)

        # TextEdit для DOCX предпросмотра (скрыт по умолчанию)
        self._docx_preview = QTextEdit()
        self._docx_preview.setReadOnly(True)
        self._docx_preview.setVisible(False)
        self._docx_preview.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                padding: 20px;
                font-family: 'Times New Roman', serif;
                font-size: 12pt;
            }
        """)
        preview_layout.addWidget(self._docx_preview)

        layout.addWidget(preview_container, stretch=1)

        # Навигация по страницам
        self._nav_widget = QWidget()
        nav_layout = QHBoxLayout(self._nav_widget)
        nav_layout.setContentsMargins(0, 10, 0, 0)

        self._prev_btn = QPushButton("<")
        self._prev_btn.setFixedSize(50, 50)
        self._prev_btn.clicked.connect(self._prev_page)
        nav_layout.addStretch()
        nav_layout.addWidget(self._prev_btn)

        self._page_label = QLabel("Страница 1 из 1")
        nav_layout.addWidget(self._page_label)

        self._next_btn = QPushButton(">")
        self._next_btn.setFixedSize(50, 50)
        self._next_btn.clicked.connect(self._next_page)
        nav_layout.addWidget(self._next_btn)
        nav_layout.addStretch()

        self._nav_widget.setVisible(False)
        layout.addWidget(self._nav_widget)

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

        # Основные настройки
        basic_group = QGroupBox("Основные настройки")
        basic_layout = QVBoxLayout(basic_group)

        # Количество копий
        copies_layout = QHBoxLayout()
        copies_layout.addWidget(QLabel("Копий:"))
        self._copies_spin = QSpinBox()
        self._copies_spin.setRange(1, 99)
        self._copies_spin.setValue(1)
        self._copies_spin.valueChanged.connect(self._update_settings)
        copies_layout.addWidget(self._copies_spin)
        copies_layout.addStretch()
        basic_layout.addLayout(copies_layout)

        # Размер бумаги
        basic_layout.addWidget(QLabel("Размер бумаги:"))
        self._paper_size_combo = QComboBox()
        self._paper_size_combo.addItems([
            "A4 (210 x 297 мм)",
            "Letter (216 x 279 мм)",
            "Legal (216 x 356 мм)",
            "A5 (148 x 210 мм)"
        ])
        self._paper_size_combo.currentIndexChanged.connect(self._update_settings)
        basic_layout.addWidget(self._paper_size_combo)

        # Источник бумаги
        basic_layout.addWidget(QLabel("Источник бумаги:"))
        self._paper_source_combo = QComboBox()
        self._paper_source_combo.addItems([
            "Автоматически",
            "Лоток 1 (250 листов)",
            "Ручная подача"
        ])
        self._paper_source_combo.currentIndexChanged.connect(self._update_settings)
        basic_layout.addWidget(self._paper_source_combo)

        # Качество печати
        basic_layout.addWidget(QLabel("Качество печати:"))
        self._quality_combo = QComboBox()
        self._quality_combo.addItems([
            "Черновик (600 dpi)",
            "Нормальное",
            "Высокое (FastRes 1200)"
        ])
        self._quality_combo.setCurrentIndex(1)
        self._quality_combo.currentIndexChanged.connect(self._update_settings)
        basic_layout.addWidget(self._quality_combo)

        layout.addWidget(basic_group)

        # Дополнительные настройки
        extra_group = QGroupBox("Дополнительно")
        extra_layout = QVBoxLayout(extra_group)

        # Ориентация
        extra_layout.addWidget(QLabel("Ориентация:"))
        self._orientation_combo = QComboBox()
        self._orientation_combo.addItems(["Книжная", "Альбомная"])
        self._orientation_combo.currentIndexChanged.connect(self._update_settings)
        extra_layout.addWidget(self._orientation_combo)

        # Диапазон страниц
        extra_layout.addWidget(QLabel("Диапазон страниц:"))
        self._page_range_edit = QLineEdit()
        self._page_range_edit.setPlaceholderText("Все (например: 1-5)")
        self._page_range_edit.textChanged.connect(self._update_settings)
        extra_layout.addWidget(self._page_range_edit)

        # Масштаб
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Масштаб:"))
        self._scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._scale_slider.setRange(25, 400)
        self._scale_slider.setValue(100)
        self._scale_slider.valueChanged.connect(self._on_scale_changed)
        scale_layout.addWidget(self._scale_slider)
        self._scale_label = QLabel("100%")
        self._scale_label.setFixedWidth(50)
        scale_layout.addWidget(self._scale_label)
        extra_layout.addLayout(scale_layout)

        # Двусторонняя печать
        self._duplex_check = QCheckBox("Двусторонняя печать (ручной дуплекс)")
        self._duplex_check.stateChanged.connect(self._update_settings)
        extra_layout.addWidget(self._duplex_check)

        layout.addWidget(extra_group)

        # Настройки изображения
        image_group = QGroupBox("Настройки изображения")
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

    def _on_browse_clicked(self):
        """Обработчик выбора файла"""
        # Добавляем DOCX в фильтры если поддерживается
        if DOCX_SUPPORTED:
            file_filter = "Документы (*.pdf *.docx *.doc *.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif);;PDF файлы (*.pdf);;Word документы (*.docx *.doc);;Изображения (*.jpg *.jpeg *.png *.bmp *.tiff *.gif);;Все файлы (*.*)"
        else:
            file_filter = "Документы (*.pdf *.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif);;PDF файлы (*.pdf);;Изображения (*.jpg *.jpeg *.png *.bmp *.tiff *.gif);;Все файлы (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл для печати",
            "",
            file_filter
        )

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """Загрузить файл для предпросмотра"""
        self._current_file = file_path
        self._file_path_edit.setText(file_path)
        logger.info(f"Загружен файл: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        # Скрываем все виджеты предпросмотра
        self._preview_label.setVisible(False)
        self._docx_preview.setVisible(False)

        if ext == '.pdf':
            self._load_pdf(file_path)
        elif ext in ('.docx', '.doc'):
            self._load_docx(file_path)
        else:
            self._load_image(file_path)

        self._print_btn.setEnabled(True)

    def _load_pdf(self, file_path: str):
        """Загрузить PDF для предпросмотра"""
        try:
            self._pdf_document = fitz.open(file_path)
            self._total_pages = len(self._pdf_document)
            self._current_page = 0
            self._docx_text = None
            self._original_image = None
            self._nav_widget.setVisible(self._total_pages > 1)
            self._preview_label.setVisible(True)
            self._update_page_info()
            self._render_pdf_page()
            logger.info(f"PDF загружен: {self._total_pages} страниц")
        except Exception as e:
            logger.error(f"Ошибка открытия PDF: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть PDF: {e}")

    def _load_docx(self, file_path: str):
        """Загрузить DOCX для предпросмотра"""
        if not DOCX_SUPPORTED:
            self._preview_label.setVisible(True)
            self._preview_label.setText("Для предпросмотра DOCX установите:\npip install python-docx")
            logger.warning("python-docx не установлен")
            return

        try:
            doc = DocxDocument(file_path)
            self._pdf_document = None
            self._original_image = None
            self._nav_widget.setVisible(False)

            # Извлекаем текст из документа
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)

            # Также извлекаем текст из таблиц
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        row_text.append(cell.text)
                    full_text.append(" | ".join(row_text))

            self._docx_text = "\n".join(full_text)

            # Показываем предпросмотр текста
            self._docx_preview.setPlainText(self._docx_text)
            self._docx_preview.setVisible(True)

            # Подсчитываем примерное количество страниц
            lines = self._docx_text.count('\n') + 1
            self._total_pages = max(1, lines // 50)  # Примерно 50 строк на страницу

            logger.info(f"DOCX загружен: ~{self._total_pages} страниц")
        except Exception as e:
            logger.error(f"Ошибка открытия DOCX: {e}")
            self._preview_label.setVisible(True)
            self._preview_label.setText(f"Ошибка открытия документа:\n{e}")

    def _load_image(self, file_path: str):
        """Загрузить изображение для предпросмотра"""
        try:
            self._original_image = Image.open(file_path)
            self._pdf_document = None
            self._docx_text = None
            self._total_pages = 1
            self._current_page = 0
            self._nav_widget.setVisible(False)
            self._preview_label.setVisible(True)
            self._update_preview_image()
            logger.info(f"Изображение загружено: {self._original_image.size}")
        except Exception as e:
            logger.error(f"Ошибка открытия изображения: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть изображение: {e}")

    def _render_pdf_page(self):
        """Отрисовать текущую страницу PDF"""
        if not self._pdf_document:
            return

        page = self._pdf_document[self._current_page]
        # Увеличиваем разрешение для лучшего качества
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)

        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)

        # Масштабируем под размер виджета
        scaled = pixmap.scaled(
            self._preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._preview_label.setPixmap(scaled)

    def _update_preview_image(self):
        """Обновить предпросмотр изображения"""
        if not self._original_image:
            return

        # Применяем настройки если есть
        image = self._original_image
        if self._settings.image_adjustments.has_changes:
            image = self._image_processing.apply_adjustments(image, self._settings.image_adjustments)

        # Конвертируем PIL Image в QPixmap
        if image.mode == 'RGBA':
            data = image.tobytes('raw', 'RGBA')
            qimg = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888)
        else:
            image = image.convert('RGB')
            data = image.tobytes('raw', 'RGB')
            qimg = QImage(data, image.width, image.height, QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self._preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._preview_label.setPixmap(scaled)

    def _prev_page(self):
        """Предыдущая страница"""
        if self._current_page > 0:
            self._current_page -= 1
            self._update_page_info()
            self._render_pdf_page()

    def _next_page(self):
        """Следующая страница"""
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self._update_page_info()
            self._render_pdf_page()

    def _update_page_info(self):
        """Обновить информацию о страницах"""
        self._page_label.setText(f"Страница {self._current_page + 1} из {self._total_pages}")
        self._prev_btn.setEnabled(self._current_page > 0)
        self._next_btn.setEnabled(self._current_page < self._total_pages - 1)

    def _update_settings(self):
        """Обновить настройки печати"""
        self._settings.copies = self._copies_spin.value()

        paper_sizes = [PaperSize.A4, PaperSize.LETTER, PaperSize.LEGAL, PaperSize.A5]
        self._settings.paper_size = paper_sizes[self._paper_size_combo.currentIndex()]

        paper_sources = [PaperSource.AUTO, PaperSource.TRAY1, PaperSource.MANUAL_FEED]
        self._settings.paper_source = paper_sources[self._paper_source_combo.currentIndex()]

        qualities = [PrintQuality.DRAFT, PrintQuality.NORMAL, PrintQuality.HIGH]
        self._settings.quality = qualities[self._quality_combo.currentIndex()]

        orientations = [PageOrientation.PORTRAIT, PageOrientation.LANDSCAPE]
        self._settings.orientation = orientations[self._orientation_combo.currentIndex()]

        page_range = self._page_range_edit.text().strip()
        self._settings.page_range = page_range if page_range else None

        self._settings.duplex = DuplexMode.MANUAL_DUPLEX if self._duplex_check.isChecked() else DuplexMode.NONE

    def _on_scale_changed(self, value: int):
        """Обработчик изменения масштаба"""
        self._scale_label.setText(f"{value}%")
        self._settings.scale = value

    def _on_image_adjustment_changed(self):
        """Обработчик изменения настроек изображения"""
        self._brightness_label.setText(str(self._brightness_slider.value()))
        self._contrast_label.setText(str(self._contrast_slider.value()))
        self._sharpness_label.setText(str(self._sharpness_slider.value()))

        self._settings.image_adjustments.brightness = self._brightness_slider.value()
        self._settings.image_adjustments.contrast = self._contrast_slider.value()
        self._settings.image_adjustments.sharpness = self._sharpness_slider.value()

        # Обновляем предпросмотр для изображений
        if self._original_image:
            self._update_preview_image()

    def _reset_image_settings(self):
        """Сбросить настройки изображения"""
        self._brightness_slider.setValue(0)
        self._contrast_slider.setValue(0)
        self._sharpness_slider.setValue(0)
        self._settings.image_adjustments.reset()

        if self._original_image:
            self._update_preview_image()

    def _on_print_clicked(self):
        """Обработчик нажатия кнопки печати"""
        if not self._current_file:
            return

        logger.info(f"Начата печать: {self._current_file}")
        self._print_btn.setEnabled(False)
        self._print_btn.setText("Печать...")

        self._print_worker = PrintWorker(self._printer_service, self._current_file, self._settings)
        self._print_worker.finished.connect(self._on_print_finished)
        self._print_worker.start()

    @pyqtSlot(bool, str)
    def _on_print_finished(self, success: bool, message: str):
        """Обработчик завершения печати"""
        self._print_btn.setEnabled(True)
        self._print_btn.setText("ПЕЧАТЬ")

        if success:
            logger.info("Печать успешно отправлена")
            QMessageBox.information(self, "Успех", message)
        else:
            logger.error(f"Ошибка печати: {message}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка печати: {message}")

    def closeEvent(self, event):
        """Очистка ресурсов при закрытии"""
        if self._pdf_document:
            self._pdf_document.close()
        super().closeEvent(event)
