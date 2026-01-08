"""
Диалог настроек печати
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSlider,
    QCheckBox, QGroupBox, QSpinBox, QLineEdit, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt

from .styles import Styles
from ..models import (
    PrintSettings, PaperSize, PaperSource, PrintQuality,
    DuplexMode, PageOrientation
)
from ..services.settings_storage import settings_storage


class PrintSettingsDialog(QDialog):
    """Диалог настроек печати"""

    def __init__(self, settings: PrintSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Настройки печати")
        self.setMinimumSize(650, 750)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("⚙️ Настройки печати")
        title.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_TITLE}px;
            font-weight: bold;
            color: {Styles.TEXT_PRIMARY};
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Прокручиваемая область с настройками
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        # === Основные настройки ===
        basic_group = QGroupBox("Основные")
        basic_layout = QVBoxLayout(basic_group)
        basic_layout.setSpacing(15)

        # Количество копий
        copies_layout = QHBoxLayout()
        copies_label = QLabel("Количество копий:")
        copies_label.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        copies_layout.addWidget(copies_label)
        copies_layout.addStretch()

        self._copies_spin = QSpinBox()
        self._copies_spin.setRange(1, 99)
        self._copies_spin.setValue(1)
        self._copies_spin.setFixedWidth(120)
        copies_layout.addWidget(self._copies_spin)
        basic_layout.addLayout(copies_layout)

        # Размер бумаги
        paper_layout = QHBoxLayout()
        paper_label = QLabel("Размер бумаги:")
        paper_label.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        paper_layout.addWidget(paper_label)
        paper_layout.addStretch()

        self._paper_combo = QComboBox()
        self._paper_combo.addItems([
            "А4 (обычный)",
            "Letter (американский)",
            "Legal (юридический)",
            "А5 (маленький)"
        ])
        self._paper_combo.setFixedWidth(250)
        paper_layout.addWidget(self._paper_combo)
        basic_layout.addLayout(paper_layout)

        # Качество печати
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Качество:")
        quality_label.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        quality_layout.addWidget(quality_label)
        quality_layout.addStretch()

        self._quality_combo = QComboBox()
        self._quality_combo.addItems([
            "Черновик (быстро, экономно)",
            "Обычное (рекомендуется)",
            "Высокое (для фото)"
        ])
        self._quality_combo.setCurrentIndex(1)
        self._quality_combo.setFixedWidth(250)
        quality_layout.addWidget(self._quality_combo)
        basic_layout.addLayout(quality_layout)

        layout.addWidget(basic_group)

        # === Дополнительные настройки ===
        extra_group = QGroupBox("Дополнительно")
        extra_layout = QVBoxLayout(extra_group)
        extra_layout.setSpacing(15)

        # Ориентация
        orient_layout = QHBoxLayout()
        orient_label = QLabel("Ориентация:")
        orient_label.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        orient_layout.addWidget(orient_label)
        orient_layout.addStretch()

        self._orientation_combo = QComboBox()
        self._orientation_combo.addItems([
            "📄 Книжная (вертикально)",
            "📄 Альбомная (горизонтально)"
        ])
        self._orientation_combo.setFixedWidth(280)
        orient_layout.addWidget(self._orientation_combo)
        extra_layout.addLayout(orient_layout)

        # Откуда брать бумагу
        source_layout = QHBoxLayout()
        source_label = QLabel("Откуда бумага:")
        source_label.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        source_layout.addWidget(source_label)
        source_layout.addStretch()

        self._source_combo = QComboBox()
        self._source_combo.addItems([
            "Автоматически",
            "Из лотка",
            "Вставить вручную"
        ])
        self._source_combo.setFixedWidth(250)
        source_layout.addWidget(self._source_combo)
        extra_layout.addLayout(source_layout)

        # Диапазон страниц
        pages_layout = QHBoxLayout()
        pages_label = QLabel("Какие страницы:")
        pages_label.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        pages_layout.addWidget(pages_label)
        pages_layout.addStretch()

        self._pages_edit = QLineEdit()
        self._pages_edit.setPlaceholderText("Все (или 1-5, 3, 7)")
        self._pages_edit.setFixedWidth(250)
        pages_layout.addWidget(self._pages_edit)
        extra_layout.addLayout(pages_layout)

        # Масштаб
        scale_layout = QHBoxLayout()
        scale_label = QLabel("Размер на бумаге:")
        scale_label.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        scale_layout.addWidget(scale_label)

        self._scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._scale_slider.setRange(25, 200)
        self._scale_slider.setValue(100)
        self._scale_slider.setFixedWidth(150)
        self._scale_slider.valueChanged.connect(self._on_scale_changed)
        scale_layout.addWidget(self._scale_slider)

        self._scale_label = QLabel("100% (обычный)")
        self._scale_label.setFixedWidth(140)
        scale_layout.addWidget(self._scale_label)

        scale_layout.addStretch()
        extra_layout.addLayout(scale_layout)

        # Двусторонняя печать
        self._duplex_check = QCheckBox("Печатать с двух сторон листа")
        self._duplex_check.setStyleSheet(f"font-size: {Styles.FONT_SIZE_NORMAL}px;")
        extra_layout.addWidget(self._duplex_check)

        layout.addWidget(extra_group)

        # === Настройки изображения ===
        image_group = QGroupBox("Коррекция изображения")
        image_layout = QVBoxLayout(image_group)
        image_layout.setSpacing(15)

        # Яркость
        brightness_layout = QHBoxLayout()
        br_label = QLabel("Яркость:")
        br_label.setFixedWidth(100)
        brightness_layout.addWidget(br_label)
        self._brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self._brightness_slider.setRange(-50, 50)
        self._brightness_slider.setValue(0)
        self._brightness_slider.valueChanged.connect(self._on_brightness_changed)
        brightness_layout.addWidget(self._brightness_slider)
        self._brightness_label = QLabel("0")
        self._brightness_label.setFixedWidth(50)
        self._brightness_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brightness_layout.addWidget(self._brightness_label)
        image_layout.addLayout(brightness_layout)

        # Контраст
        contrast_layout = QHBoxLayout()
        ct_label = QLabel("Контраст:")
        ct_label.setFixedWidth(100)
        contrast_layout.addWidget(ct_label)
        self._contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self._contrast_slider.setRange(-50, 50)
        self._contrast_slider.setValue(0)
        self._contrast_slider.valueChanged.connect(self._on_contrast_changed)
        contrast_layout.addWidget(self._contrast_slider)
        self._contrast_label = QLabel("0")
        self._contrast_label.setFixedWidth(50)
        self._contrast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contrast_layout.addWidget(self._contrast_label)
        image_layout.addLayout(contrast_layout)

        # Кнопка сброса
        reset_btn = QPushButton("Сбросить настройки изображения")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.TEXT_SECONDARY};
                font-size: {Styles.FONT_SIZE_SMALL}px;
                min-height: 40px;
            }}
        """)
        reset_btn.clicked.connect(self._reset_image)
        image_layout.addWidget(reset_btn)

        layout.addWidget(image_group)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll, stretch=1)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: {Styles.TEXT_PRIMARY};
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                padding: 18px 40px;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        buttons_layout.addStretch()

        save_btn = QPushButton("✓ Сохранить")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.SUCCESS_COLOR};
                color: white;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                padding: 18px 50px;
            }}
        """)
        save_btn.clicked.connect(self._save_and_close)
        buttons_layout.addWidget(save_btn)

        main_layout.addLayout(buttons_layout)

    def _load_settings(self):
        """Загрузить текущие настройки в форму"""
        self._copies_spin.setValue(self._settings.copies)

        paper_index = {
            PaperSize.A4: 0,
            PaperSize.LETTER: 1,
            PaperSize.LEGAL: 2,
            PaperSize.A5: 3
        }.get(self._settings.paper_size, 0)
        self._paper_combo.setCurrentIndex(paper_index)

        quality_index = {
            PrintQuality.DRAFT: 0,
            PrintQuality.NORMAL: 1,
            PrintQuality.HIGH: 2
        }.get(self._settings.quality, 1)
        self._quality_combo.setCurrentIndex(quality_index)

        orient_index = 0 if self._settings.orientation == PageOrientation.PORTRAIT else 1
        self._orientation_combo.setCurrentIndex(orient_index)

        source_index = {
            PaperSource.AUTO: 0,
            PaperSource.TRAY1: 1,
            PaperSource.MANUAL_FEED: 2
        }.get(self._settings.paper_source, 0)
        self._source_combo.setCurrentIndex(source_index)

        if self._settings.page_range:
            self._pages_edit.setText(self._settings.page_range)

        self._scale_slider.setValue(self._settings.scale)

        self._duplex_check.setChecked(self._settings.duplex == DuplexMode.MANUAL_DUPLEX)

        self._brightness_slider.setValue(self._settings.image_adjustments.brightness)
        self._contrast_slider.setValue(self._settings.image_adjustments.contrast)

    def _on_scale_changed(self, value: int):
        """Обработчик изменения масштаба"""
        if value < 80:
            text = f"{value}% (уменьшено)"
        elif value > 120:
            text = f"{value}% (увеличено)"
        else:
            text = f"{value}% (обычный)"
        self._scale_label.setText(text)

    def _on_brightness_changed(self, value: int):
        self._brightness_label.setText(str(value))

    def _on_contrast_changed(self, value: int):
        self._contrast_label.setText(str(value))

    def _reset_image(self):
        """Сбросить настройки изображения"""
        self._brightness_slider.setValue(0)
        self._contrast_slider.setValue(0)

    def _save_and_close(self):
        """Сохранить настройки и закрыть"""
        self._settings.copies = self._copies_spin.value()

        paper_sizes = [PaperSize.A4, PaperSize.LETTER, PaperSize.LEGAL, PaperSize.A5]
        self._settings.paper_size = paper_sizes[self._paper_combo.currentIndex()]

        qualities = [PrintQuality.DRAFT, PrintQuality.NORMAL, PrintQuality.HIGH]
        self._settings.quality = qualities[self._quality_combo.currentIndex()]

        orientations = [PageOrientation.PORTRAIT, PageOrientation.LANDSCAPE]
        self._settings.orientation = orientations[self._orientation_combo.currentIndex()]

        sources = [PaperSource.AUTO, PaperSource.TRAY1, PaperSource.MANUAL_FEED]
        self._settings.paper_source = sources[self._source_combo.currentIndex()]

        page_range = self._pages_edit.text().strip()
        self._settings.page_range = page_range if page_range else None

        self._settings.scale = self._scale_slider.value()

        self._settings.duplex = DuplexMode.MANUAL_DUPLEX if self._duplex_check.isChecked() else DuplexMode.NONE

        self._settings.image_adjustments.brightness = self._brightness_slider.value()
        self._settings.image_adjustments.contrast = self._contrast_slider.value()

        # Сохраняем в настройки пользователя
        prefs = settings_storage.preferences
        prefs.default_copies = self._settings.copies
        prefs.default_paper_size = self._paper_combo.currentIndex()
        prefs.default_quality = self._quality_combo.currentIndex()
        settings_storage.save()

        self.accept()

    def get_settings(self) -> PrintSettings:
        """Получить настройки"""
        return self._settings

    @staticmethod
    def edit_settings(settings: PrintSettings, parent=None) -> bool:
        """Показать диалог редактирования настроек"""
        dialog = PrintSettingsDialog(settings, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
