"""
Упрощённый диалог выбора файла для пожилых пользователей
"""

import os
from pathlib import Path
from typing import Optional, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QSize

from .styles import Styles
from ..services.settings_storage import settings_storage


class FilePickerDialog(QDialog):
    """Упрощённый диалог выбора файла"""

    SUPPORTED_EXTENSIONS = {
        '.pdf': ('📄', 'PDF документ'),
        '.docx': ('📝', 'Word документ'),
        '.doc': ('📝', 'Word документ'),
        '.jpg': ('🖼️', 'Изображение'),
        '.jpeg': ('🖼️', 'Изображение'),
        '.png': ('🖼️', 'Изображение'),
        '.bmp': ('🖼️', 'Изображение'),
        '.tiff': ('🖼️', 'Изображение'),
        '.tif': ('🖼️', 'Изображение'),
        '.gif': ('🖼️', 'Изображение'),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_file: Optional[str] = None
        self._init_ui()
        self._load_recent_files()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Выберите файл для печати")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("Выберите файл для печати")
        title.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_TITLE}px;
            font-weight: bold;
            color: {Styles.TEXT_PRIMARY};
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Быстрый доступ к папкам
        quick_access = QFrame()
        quick_access.setStyleSheet(Styles.get_card_style())
        quick_layout = QHBoxLayout(quick_access)
        quick_layout.setSpacing(15)

        # Кнопки быстрого доступа
        folders = [
            ("🏠 Рабочий стол", self._get_desktop_path()),
            ("📁 Документы", str(Path.home() / "Documents")),
            ("📥 Загрузки", str(Path.home() / "Downloads")),
        ]

        for name, path in folders:
            if os.path.exists(path):
                btn = QPushButton(name)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #E3F2FD;
                        color: {Styles.TEXT_PRIMARY};
                        border: 2px solid {Styles.PRIMARY_COLOR};
                        border-radius: 12px;
                        padding: 15px 25px;
                        font-size: {Styles.FONT_SIZE_NORMAL}px;
                        font-weight: 500;
                        min-height: 30px;
                    }}
                    QPushButton:hover {{
                        background-color: #BBDEFB;
                    }}
                """)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda checked, p=path: self._open_folder(p))
                quick_layout.addWidget(btn)

        quick_layout.addStretch()
        layout.addWidget(quick_access)

        # Недавние файлы
        recent_label = QLabel("📋 Недавние файлы:")
        recent_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_LARGE}px;
            font-weight: bold;
            color: {Styles.TEXT_PRIMARY};
            margin-top: 10px;
        """)
        layout.addWidget(recent_label)

        # Список недавних файлов
        self._recent_list = QListWidget()
        self._recent_list.setStyleSheet(f"""
            QListWidget {{
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 12px;
                padding: 10px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
            }}
            QListWidget::item {{
                padding: 15px;
                border-bottom: 1px solid #EEEEEE;
                border-radius: 8px;
            }}
            QListWidget::item:hover {{
                background-color: #E3F2FD;
            }}
            QListWidget::item:selected {{
                background-color: {Styles.PRIMARY_COLOR};
                color: white;
            }}
        """)
        self._recent_list.setSpacing(5)
        self._recent_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._recent_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._recent_list, stretch=1)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Кнопка "Найти в папках"
        browse_btn = QPushButton("📂 Найти в папках...")
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.TEXT_SECONDARY};
                color: white;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                border-radius: 12px;
                padding: 20px 40px;
            }}
            QPushButton:hover {{
                background-color: #5D5D5D;
            }}
        """)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_files)
        buttons_layout.addWidget(browse_btn)

        buttons_layout.addStretch()

        # Кнопка "Отмена"
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: {Styles.TEXT_PRIMARY};
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                border-radius: 12px;
                padding: 20px 40px;
            }}
            QPushButton:hover {{
                background-color: #BDBDBD;
            }}
        """)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        # Кнопка "Выбрать"
        self._select_btn = QPushButton("✓ Выбрать этот файл")
        self._select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.SUCCESS_COLOR};
                color: white;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                border-radius: 12px;
                padding: 20px 40px;
            }}
            QPushButton:hover {{
                background-color: #1B5E20;
            }}
            QPushButton:disabled {{
                background-color: #9E9E9E;
            }}
        """)
        self._select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._select_btn.setEnabled(False)
        self._select_btn.clicked.connect(self._confirm_selection)
        buttons_layout.addWidget(self._select_btn)

        layout.addLayout(buttons_layout)

    def _get_desktop_path(self) -> str:
        """Получить путь к рабочему столу"""
        import platform
        if platform.system() == "Windows":
            return os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        return str(Path.home() / "Desktop")

    def _load_recent_files(self):
        """Загрузить список недавних файлов"""
        self._recent_list.clear()

        recent = settings_storage.get_recent_files()

        if not recent:
            # Показываем подсказку
            item = QListWidgetItem("    Здесь появятся недавно открытые файлы")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._recent_list.addItem(item)
            return

        for file_path in recent:
            ext = os.path.splitext(file_path)[1].lower()
            icon, type_name = self.SUPPORTED_EXTENSIONS.get(ext, ('📄', 'Файл'))

            file_name = os.path.basename(file_path)
            folder = os.path.dirname(file_path)

            # Сокращаем путь если слишком длинный
            if len(folder) > 50:
                folder = "..." + folder[-47:]

            item = QListWidgetItem(f"{icon}  {file_name}\n      📁 {folder}")
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setSizeHint(QSize(0, 70))
            self._recent_list.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem):
        """Обработчик клика по элементу"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            self._selected_file = file_path
            self._select_btn.setEnabled(True)
        else:
            self._select_btn.setEnabled(False)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Обработчик двойного клика - сразу выбираем файл"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            self._selected_file = file_path
            self.accept()

    def _open_folder(self, folder_path: str):
        """Открыть стандартный диалог в указанной папке"""
        file_filter = "Документы (*.pdf *.docx *.doc *.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif);;Все файлы (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            folder_path,
            file_filter
        )

        if file_path:
            self._selected_file = file_path
            self.accept()

    def _browse_files(self):
        """Открыть стандартный диалог выбора файла"""
        start_folder = settings_storage.preferences.last_print_folder
        if not start_folder or not os.path.exists(start_folder):
            start_folder = str(Path.home() / "Documents")

        file_filter = "Документы (*.pdf *.docx *.doc *.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif);;Все файлы (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            start_folder,
            file_filter
        )

        if file_path:
            self._selected_file = file_path
            self.accept()

    def _confirm_selection(self):
        """Подтвердить выбор файла"""
        if self._selected_file and os.path.exists(self._selected_file):
            self.accept()

    def get_selected_file(self) -> Optional[str]:
        """Получить выбранный файл"""
        return self._selected_file

    @staticmethod
    def get_file(parent=None) -> Optional[str]:
        """Статический метод для получения файла"""
        dialog = FilePickerDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_file()
        return None
