"""
Представление настроек с логами
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QTextEdit, QFrame, QMessageBox,
    QGroupBox, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor

from .styles import Styles
from ..services import logger, UpdateService


class UpdateWorker(QThread):
    """Рабочий поток для обновления"""
    finished = pyqtSignal(bool, str)
    checking = pyqtSignal(str)

    def __init__(self, update_service: UpdateService, action: str = "check"):
        super().__init__()
        self.update_service = update_service
        self.action = action

    def run(self):
        if self.action == "check":
            self.checking.emit("Проверка обновлений...")
            has_updates, message = self.update_service.check_for_updates()
            self.finished.emit(has_updates, message)
        elif self.action == "update":
            self.checking.emit("Загрузка обновлений...")
            success, message = self.update_service.update()
            self.finished.emit(success, message)


class SettingsView(QWidget):
    """Представление настроек"""

    navigate_back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._update_service = UpdateService()
        self._update_worker = None

        self._init_ui()

        # Подписываемся на логи
        logger.add_log_callback(self._on_new_log)

        # Загружаем существующие логи
        self._log_text.setPlainText(logger.get_all_logs())
        self._scroll_to_bottom()

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

        title_label = QLabel("НАСТРОЙКИ")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        header_layout.addSpacing(100)

        main_layout.addLayout(header_layout)

        # Вкладки
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #F5F5F5;
            }
        """)

        # Вкладка "Обновления"
        update_tab = self._create_update_tab()
        tab_widget.addTab(update_tab, "Обновления")

        # Вкладка "Логи"
        logs_tab = self._create_logs_tab()
        tab_widget.addTab(logs_tab, "Логи")

        # Вкладка "О программе"
        about_tab = self._create_about_tab()
        tab_widget.addTab(about_tab, "О программе")

        main_layout.addWidget(tab_widget)

    def _create_update_tab(self) -> QWidget:
        """Создать вкладку обновлений"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Информация о версии
        version_group = QGroupBox("Текущая версия")
        version_layout = QVBoxLayout(version_group)

        self._version_label = QLabel(f"Версия: {self._update_service.get_current_version()}")
        self._version_label.setStyleSheet("font-size: 16px;")
        version_layout.addWidget(self._version_label)

        self._commit_label = QLabel(f"Коммит: {self._update_service.get_last_commit_info()}")
        self._commit_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY};")
        self._commit_label.setWordWrap(True)
        version_layout.addWidget(self._commit_label)

        layout.addWidget(version_group)

        # Статус обновления
        status_group = QGroupBox("Обновление")
        status_layout = QVBoxLayout(status_group)

        self._update_status_label = QLabel("Нажмите 'Проверить обновления' для проверки")
        self._update_status_label.setStyleSheet("font-size: 14px;")
        self._update_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self._update_status_label)

        self._update_progress = QProgressBar()
        self._update_progress.setVisible(False)
        self._update_progress.setRange(0, 0)  # Индикатор загрузки
        status_layout.addWidget(self._update_progress)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self._check_btn = QPushButton("Проверить обновления")
        self._check_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.PRIMARY_COLOR};
                color: white;
                padding: 15px 30px;
                font-size: 14px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
            }}
        """)
        self._check_btn.clicked.connect(self._check_updates)
        buttons_layout.addWidget(self._check_btn)

        self._update_btn = QPushButton("Обновить")
        self._update_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.SUCCESS_COLOR};
                color: white;
                padding: 15px 30px;
                font-size: 14px;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #43A047;
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
            }}
        """)
        self._update_btn.setEnabled(False)
        self._update_btn.clicked.connect(self._do_update)
        buttons_layout.addWidget(self._update_btn)

        status_layout.addLayout(buttons_layout)
        layout.addWidget(status_group)

        layout.addStretch()
        return widget

    def _create_logs_tab(self) -> QWidget:
        """Создать вкладку логов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Описание
        desc_label = QLabel("Журнал событий приложения. Скопируйте логи для отправки разработчику при возникновении ошибок.")
        desc_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY};")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Текстовое поле с логами
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self._log_text, stretch=1)

        # Кнопки
        buttons_layout = QHBoxLayout()

        copy_btn = QPushButton("Копировать логи")
        copy_btn.setStyleSheet(f"background-color: {Styles.PRIMARY_COLOR};")
        copy_btn.clicked.connect(self._copy_logs)
        buttons_layout.addWidget(copy_btn)

        clear_btn = QPushButton("Очистить")
        clear_btn.setStyleSheet(f"background-color: {Styles.TEXT_SECONDARY};")
        clear_btn.clicked.connect(self._clear_logs)
        buttons_layout.addWidget(clear_btn)

        open_folder_btn = QPushButton("Открыть папку логов")
        open_folder_btn.setStyleSheet(f"background-color: {Styles.TEXT_SECONDARY};")
        open_folder_btn.clicked.connect(self._open_logs_folder)
        buttons_layout.addWidget(open_folder_btn)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        # Путь к файлу лога
        log_path_label = QLabel(f"Файл лога: {logger.get_log_file_path()}")
        log_path_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(log_path_label)

        return widget

    def _create_about_tab(self) -> QWidget:
        """Создать вкладку 'О программе'"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Название
        name_label = QLabel("EasyPrinter")
        name_font = QFont()
        name_font.setPointSize(32)
        name_font.setBold(True)
        name_label.setFont(name_font)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # Версия
        version_label = QLabel("Версия 1.0.0")
        version_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 16px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # Описание
        desc_label = QLabel("Приложение для управления принтером\nHP LaserJet M1536dnf MFP")
        desc_label.setStyleSheet("font-size: 14px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        layout.addSpacing(20)

        # Возможности
        features_label = QLabel("Печать • Сканирование • Копирование • Мониторинг статуса")
        features_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY};")
        features_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(features_label)

        layout.addStretch()

        # Технологии
        tech_label = QLabel("Python 3 • PyQt6 • Pillow • PyMuPDF")
        tech_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 12px;")
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tech_label)

        return widget

    def _check_updates(self):
        """Проверить обновления"""
        self._check_btn.setEnabled(False)
        self._update_btn.setEnabled(False)
        self._update_progress.setVisible(True)

        self._update_worker = UpdateWorker(self._update_service, "check")
        self._update_worker.checking.connect(self._on_update_checking)
        self._update_worker.finished.connect(self._on_check_finished)
        self._update_worker.start()

    @pyqtSlot(str)
    def _on_update_checking(self, message: str):
        """Обработчик статуса проверки"""
        self._update_status_label.setText(message)

    @pyqtSlot(bool, str)
    def _on_check_finished(self, has_updates: bool, message: str):
        """Обработчик завершения проверки"""
        self._check_btn.setEnabled(True)
        self._update_progress.setVisible(False)
        self._update_status_label.setText(message)

        if has_updates:
            self._update_btn.setEnabled(True)
            self._update_status_label.setStyleSheet(f"color: {Styles.SUCCESS_COLOR}; font-size: 14px;")
        else:
            self._update_btn.setEnabled(False)
            self._update_status_label.setStyleSheet("font-size: 14px;")

    def _do_update(self):
        """Выполнить обновление"""
        self._check_btn.setEnabled(False)
        self._update_btn.setEnabled(False)
        self._update_progress.setVisible(True)

        self._update_worker = UpdateWorker(self._update_service, "update")
        self._update_worker.checking.connect(self._on_update_checking)
        self._update_worker.finished.connect(self._on_update_finished)
        self._update_worker.start()

    @pyqtSlot(bool, str)
    def _on_update_finished(self, success: bool, message: str):
        """Обработчик завершения обновления"""
        self._check_btn.setEnabled(True)
        self._update_progress.setVisible(False)
        self._update_status_label.setText(message)

        if success:
            self._update_status_label.setStyleSheet(f"color: {Styles.SUCCESS_COLOR}; font-size: 14px;")
            QMessageBox.information(
                self, "Обновление",
                "Обновление успешно завершено!\n\nПожалуйста, перезапустите приложение для применения изменений."
            )
            # Обновляем информацию о версии
            self._version_label.setText(f"Версия: {self._update_service.get_current_version()}")
            self._commit_label.setText(f"Коммит: {self._update_service.get_last_commit_info()}")
        else:
            self._update_status_label.setStyleSheet(f"color: {Styles.DANGER_COLOR}; font-size: 14px;")
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить:\n{message}")

    def _on_new_log(self, message: str):
        """Обработчик нового лога"""
        self._log_text.append(message)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """Прокрутить логи вниз"""
        cursor = self._log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log_text.setTextCursor(cursor)

    def _copy_logs(self):
        """Копировать логи в буфер обмена"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._log_text.toPlainText())
        QMessageBox.information(self, "Скопировано", "Логи скопированы в буфер обмена")

    def _clear_logs(self):
        """Очистить логи"""
        logger.clear_buffer()
        self._log_text.clear()
        logger.info("Логи очищены пользователем")

    def _open_logs_folder(self):
        """Открыть папку с логами"""
        import os
        import platform
        import subprocess

        log_path = logger.get_log_file_path()
        folder = os.path.dirname(log_path)

        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку: {e}")

    def showEvent(self, event):
        """При показе страницы"""
        super().showEvent(event)
        # Обновляем логи
        self._log_text.setPlainText(logger.get_all_logs())
        self._scroll_to_bottom()
