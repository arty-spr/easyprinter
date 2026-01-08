"""
Диалог подтверждения печати
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt

from .styles import Styles
from ..models import PrintSettings, PaperSize


class PrintConfirmationDialog(QDialog):
    """Диалог подтверждения печати с превью"""

    def __init__(self, file_path: str, settings: PrintSettings, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._settings = settings
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Подтверждение печати")
        self.setMinimumSize(600, 450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 40, 40, 40)

        # Заголовок
        title = QLabel("Вы собираетесь распечатать:")
        title.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_TITLE}px;
            font-weight: bold;
            color: {Styles.TEXT_PRIMARY};
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Информация о файле
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            background-color: #E3F2FD;
            border-radius: 15px;
            padding: 20px;
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(15)

        # Имя файла
        file_name = os.path.basename(self._file_path)
        ext = os.path.splitext(file_name)[1].lower()

        icon = "📄"
        if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif'):
            icon = "🖼️"
        elif ext in ('.docx', '.doc'):
            icon = "📝"

        file_label = QLabel(f"{icon}  {file_name}")
        file_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_LARGE}px;
            font-weight: bold;
            color: {Styles.TEXT_PRIMARY};
        """)
        file_label.setWordWrap(True)
        info_layout.addWidget(file_label)

        # Количество копий
        copies = self._settings.copies
        if copies == 1:
            copies_text = "1 копия"
        elif copies in (2, 3, 4):
            copies_text = f"{copies} копии"
        else:
            copies_text = f"{copies} копий"
            
        copies_label = QLabel(f"📋  {copies_text}")
        copies_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_NORMAL}px;
            color: {Styles.TEXT_PRIMARY};
        """)
        info_layout.addWidget(copies_label)

        # Размер бумаги
        paper_names = {
            PaperSize.A4: "А4",
            PaperSize.LETTER: "Letter",
            PaperSize.LEGAL: "Legal",
            PaperSize.A5: "А5",
        }
        paper_name = paper_names.get(self._settings.paper_size, "А4")
        paper_label = QLabel(f"📐  Бумага: {paper_name}")
        paper_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_NORMAL}px;
            color: {Styles.TEXT_PRIMARY};
        """)
        info_layout.addWidget(paper_label)

        layout.addWidget(info_frame)

        # Разделитель
        layout.addSpacing(20)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Кнопка "Отмена"
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #E0E0E0;
                color: {Styles.TEXT_PRIMARY};
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: bold;
                border-radius: 15px;
                padding: 25px 50px;
                min-width: 200px;
            }}
            QPushButton:hover {{
                background-color: #BDBDBD;
            }}
        """)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        buttons_layout.addStretch()

        # Кнопка "Печатать"
        print_btn = QPushButton("✓ Да, печатать!")
        print_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.SUCCESS_COLOR};
                color: white;
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: bold;
                border-radius: 15px;
                padding: 25px 50px;
                min-width: 250px;
            }}
            QPushButton:hover {{
                background-color: #1B5E20;
            }}
        """)
        print_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        print_btn.clicked.connect(self.accept)
        print_btn.setDefault(True)
        buttons_layout.addWidget(print_btn)

        layout.addLayout(buttons_layout)

    @staticmethod
    def confirm(file_path: str, settings: PrintSettings, parent=None) -> bool:
        """Показать диалог и вернуть результат"""
        dialog = PrintConfirmationDialog(file_path, settings, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
