"""
Представление для печати документов (упрощённый интерфейс для пожилых)
"""

import os
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap, QImage, QFont
from PIL import Image
import fitz  # PyMuPDF for PDF preview

from .styles import Styles
from .file_picker_dialog import FilePickerDialog
from .print_settings_dialog import PrintSettingsDialog
from .print_confirmation_dialog import PrintConfirmationDialog
from ..models import PrintSettings
from ..services import PrinterService, ImageProcessingService, logger
from ..services.sound_service import sound_service
from ..services.settings_storage import settings_storage

# Попытка импорта python-docx для поддержки Word документов
try:
    from docx import Document as DocxDocument
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
    """Представление для печати с упрощённым интерфейсом"""

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
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(20)

        # Заголовок
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Назад")
        back_btn.setFixedSize(150, 60)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.TEXT_SECONDARY};
                color: white;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{ background-color: #5a6268; }}
        """)
        back_btn.clicked.connect(self.navigate_back.emit)
        header_layout.addWidget(back_btn)

        header_layout.addStretch()

        title_label = QLabel("🖨️ ПЕЧАТЬ")
        title_font = QFont()
        title_font.setPointSize(Styles.FONT_SIZE_TITLE)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        header_layout.addSpacing(150)

        main_layout.addLayout(header_layout)

        # Основной контент
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)

        # Левая панель - предпросмотр
        preview_panel = self._create_preview_panel()
        content_layout.addWidget(preview_panel, stretch=2)

        # Правая панель - действия
        actions_panel = self._create_actions_panel()
        content_layout.addWidget(actions_panel, stretch=1)

        main_layout.addLayout(content_layout)

        # Кнопка печати
        self._print_btn = QPushButton("🖨️  НАПЕЧАТАТЬ")
        self._print_btn.setFixedHeight(100)
        self._print_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.SUCCESS_COLOR};
                color: white;
                font-size: {Styles.FONT_SIZE_TITLE}px;
                font-weight: bold;
                border-radius: 15px;
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
        layout.setSpacing(15)

        # Информация о файле
        self._file_info_label = QLabel("Файл не выбран")
        self._file_info_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_LARGE}px;
            color: {Styles.TEXT_SECONDARY};
            padding: 10px;
        """)
        self._file_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._file_info_label)

        # Область предпросмотра
        preview_container = QFrame()
        preview_container.setStyleSheet("background-color: #F5F5F5; border-radius: 12px;")
        preview_layout = QVBoxLayout(preview_container)

        # Label для изображений/PDF
        self._preview_label = QLabel("Выберите файл для печати")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet(f"""
            color: {Styles.TEXT_SECONDARY};
            font-size: {Styles.FONT_SIZE_LARGE}px;
        """)
        self._preview_label.setMinimumSize(400, 450)
        self._preview_label.setScaledContents(False)
        preview_layout.addWidget(self._preview_label)

        # TextEdit для DOCX предпросмотра
        self._docx_preview = QTextEdit()
        self._docx_preview.setReadOnly(True)
        self._docx_preview.setVisible(False)
        self._docx_preview.setStyleSheet(f"""
            QTextEdit {{
                background-color: white;
                border: none;
                padding: 20px;
                font-family: 'Times New Roman', serif;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
            }}
        """)
        preview_layout.addWidget(self._docx_preview)

        layout.addWidget(preview_container, stretch=1)

        # Навигация по страницам
        self._nav_widget = QWidget()
        nav_layout = QHBoxLayout(self._nav_widget)
        nav_layout.setContentsMargins(0, 10, 0, 0)

        self._prev_btn = QPushButton("◀ Назад")
        self._prev_btn.setFixedSize(120, 50)
        self._prev_btn.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        self._prev_btn.clicked.connect(self._prev_page)
        nav_layout.addStretch()
        nav_layout.addWidget(self._prev_btn)

        self._page_label = QLabel("Страница 1 из 1")
        self._page_label.setStyleSheet(f"font-size: {Styles.FONT_SIZE_LARGE}px; margin: 0 20px;")
        nav_layout.addWidget(self._page_label)

        self._next_btn = QPushButton("Вперёд ▶")
        self._next_btn.setFixedSize(120, 50)
        self._next_btn.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        self._next_btn.clicked.connect(self._next_page)
        nav_layout.addWidget(self._next_btn)
        nav_layout.addStretch()

        self._nav_widget.setVisible(False)
        layout.addWidget(self._nav_widget)

        return frame

    def _create_actions_panel(self) -> QFrame:
        """Создать панель действий"""
        frame = QFrame()
        frame.setStyleSheet(Styles.get_card_style())
        layout = QVBoxLayout(frame)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)

        # Заголовок
        title = QLabel("Выберите файл")
        title.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_LARGE}px;
            font-weight: bold;
            color: {Styles.TEXT_PRIMARY};
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(10)

        # Кнопка выбора файла
        select_btn = QPushButton("📂  Выбрать файл")
        select_btn.setFixedHeight(80)
        select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.PRIMARY_COLOR};
                color: white;
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
        """)
        select_btn.clicked.connect(self._on_select_file_clicked)
        layout.addWidget(select_btn)

        layout.addSpacing(20)

        # Информация о копиях
        self._copies_label = QLabel("Копий: 1")
        self._copies_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_LARGE}px;
            color: {Styles.TEXT_PRIMARY};
            padding: 15px;
            background-color: #F5F5F5;
            border-radius: 8px;
        """)
        self._copies_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._copies_label)

        # Кнопка настроек печати
        settings_btn = QPushButton("⚙️  Настройки печати")
        settings_btn.setFixedHeight(70)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.TEXT_SECONDARY};
                color: white;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: #5a6268;
            }}
        """)
        settings_btn.clicked.connect(self._on_settings_clicked)
        layout.addWidget(settings_btn)

        layout.addStretch()

        # Подсказка
        hint_label = QLabel("Поддерживаемые форматы:\nPDF, Word, изображения")
        hint_label.setStyleSheet(f"""
            color: {Styles.TEXT_SECONDARY};
            font-size: {Styles.FONT_SIZE_NORMAL}px;
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        return frame

    def _on_select_file_clicked(self):
        """Открыть диалог выбора файла"""
        dialog = FilePickerDialog(self)
        if dialog.exec():
            file_path = dialog.get_selected_file()
            if file_path:
                self._load_file(file_path)

    def _on_settings_clicked(self):
        """Открыть диалог настроек печати"""
        dialog = PrintSettingsDialog(self._settings, self)
        if dialog.exec():
            self._settings = dialog.get_settings()
            self._copies_label.setText(f"Копий: {self._settings.copies}")
            logger.info(f"Настройки печати обновлены: копий={self._settings.copies}")

    def load_file_for_print(self, file_path: str):
        """Загрузить файл для печати (вызывается из drag-and-drop)"""
        self._load_file(file_path)

    def _load_file(self, file_path: str):
        """Загрузить файл для предпросмотра"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Ошибка", f"Файл не найден:\n{file_path}")
            return

        self._current_file = file_path
        file_name = os.path.basename(file_path)
        self._file_info_label.setText(f"📄 {file_name}")
        logger.info(f"Загружен файл: {file_path}")

        # Добавляем в недавние файлы
        settings_storage.add_recent_file(file_path)

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
            if self._pdf_document:
                self._pdf_document.close()
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
            self._preview_label.setVisible(True)
            self._preview_label.setText(f"Не удалось открыть PDF:\n{e}")

    def _load_docx(self, file_path: str):
        """Загрузить DOCX для предпросмотра"""
        if not DOCX_SUPPORTED:
            self._preview_label.setVisible(True)
            self._preview_label.setText("Для предпросмотра Word\nустановите python-docx")
            logger.warning("python-docx не установлен")
            return

        try:
            doc = DocxDocument(file_path)
            if self._pdf_document:
                self._pdf_document.close()
            self._pdf_document = None
            self._original_image = None
            self._nav_widget.setVisible(False)

            # Извлекаем текст
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)

            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text for cell in row.cells]
                    full_text.append(" | ".join(row_text))

            self._docx_text = "\n".join(full_text)
            self._docx_preview.setPlainText(self._docx_text)
            self._docx_preview.setVisible(True)

            lines = self._docx_text.count('\n') + 1
            self._total_pages = max(1, lines // 50)

            logger.info(f"DOCX загружен: ~{self._total_pages} страниц")
        except Exception as e:
            logger.error(f"Ошибка открытия DOCX: {e}")
            self._preview_label.setVisible(True)
            self._preview_label.setText(f"Ошибка открытия документа:\n{e}")

    def _load_image(self, file_path: str):
        """Загрузить изображение для предпросмотра"""
        try:
            self._original_image = Image.open(file_path)
            if self._pdf_document:
                self._pdf_document.close()
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
            self._preview_label.setVisible(True)
            self._preview_label.setText(f"Не удалось открыть изображение:\n{e}")

    def _render_pdf_page(self):
        """Отрисовать текущую страницу PDF"""
        if not self._pdf_document:
            return

        page = self._pdf_document[self._current_page]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)

        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(img)

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

        image = self._original_image
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

    def _on_print_clicked(self):
        """Обработчик нажатия кнопки печати"""
        if not self._current_file:
            return

        # Показываем диалог подтверждения
        file_name = os.path.basename(self._current_file)
        dialog = PrintConfirmationDialog(file_name, self._settings, self)

        if dialog.exec():
            logger.info(f"Печать подтверждена: {self._current_file}")
            self._start_printing()
        else:
            logger.info("Печать отменена пользователем")

    def _start_printing(self):
        """Начать печать"""
        self._print_btn.setEnabled(False)
        self._print_btn.setText("⏳ Печатаем...")

        self._print_worker = PrintWorker(self._printer_service, self._current_file, self._settings)
        self._print_worker.finished.connect(self._on_print_finished)
        self._print_worker.start()

    @pyqtSlot(bool, str)
    def _on_print_finished(self, success: bool, message: str):
        """Обработчик завершения печати"""
        self._print_btn.setEnabled(True)
        self._print_btn.setText("🖨️  НАПЕЧАТАТЬ")

        if success:
            logger.info("Печать успешно отправлена")
            sound_service.play_success()

            msg = QMessageBox(self)
            msg.setWindowTitle("Готово!")
            msg.setText("Документ отправлен на печать")
            msg.setInformativeText("Заберите распечатку из лотка принтера")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    font-size: {Styles.FONT_SIZE_LARGE}px;
                }}
                QMessageBox QLabel {{
                    font-size: {Styles.FONT_SIZE_LARGE}px;
                    min-width: 400px;
                }}
                QPushButton {{
                    font-size: {Styles.FONT_SIZE_NORMAL}px;
                    min-width: 150px;
                    min-height: 50px;
                }}
            """)
            msg.exec()
        else:
            logger.error(f"Ошибка печати: {message}")
            sound_service.play_error()

            msg = QMessageBox(self)
            msg.setWindowTitle("Ошибка")
            msg.setText("Не удалось напечатать документ")
            msg.setInformativeText(f"Ошибка: {message}")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    font-size: {Styles.FONT_SIZE_LARGE}px;
                }}
                QMessageBox QLabel {{
                    font-size: {Styles.FONT_SIZE_LARGE}px;
                    min-width: 400px;
                }}
                QPushButton {{
                    font-size: {Styles.FONT_SIZE_NORMAL}px;
                    min-width: 150px;
                    min-height: 50px;
                }}
            """)
            msg.exec()

    def closeEvent(self, event):
        """Очистка ресурсов"""
        if self._pdf_document:
            self._pdf_document.close()
        super().closeEvent(event)
