"""
Сервис логирования для EasyPrinter
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Callable
from io import StringIO


class LoggerService:
    """Централизованный сервис логирования"""

    _instance = None
    _log_buffer: List[str] = []
    _log_callbacks: List[Callable[[str], None]] = []
    _max_buffer_size = 1000

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Папка для логов
        self._log_dir = Path.home() / ".easyprinter" / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Файл лога
        self._log_file = self._log_dir / f"easyprinter_{datetime.now().strftime('%Y-%m-%d')}.log"

        # Настройка логгера
        self._logger = logging.getLogger("EasyPrinter")
        self._logger.setLevel(logging.DEBUG)

        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Файловый обработчик
        file_handler = logging.FileHandler(self._log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        # Обработчик для буфера (чтобы показывать в GUI)
        self._string_handler = logging.StreamHandler(StringIO())
        self._string_handler.setLevel(logging.DEBUG)
        self._string_handler.setFormatter(formatter)

        # Кастомный обработчик для callback
        class CallbackHandler(logging.Handler):
            def __init__(self, service):
                super().__init__()
                self.service = service

            def emit(self, record):
                msg = self.format(record)
                self.service._add_to_buffer(msg)

        callback_handler = CallbackHandler(self)
        callback_handler.setLevel(logging.DEBUG)
        callback_handler.setFormatter(formatter)
        self._logger.addHandler(callback_handler)

        self.info("=== EasyPrinter запущен ===")

    def _add_to_buffer(self, message: str):
        """Добавить сообщение в буфер"""
        self._log_buffer.append(message)
        if len(self._log_buffer) > self._max_buffer_size:
            self._log_buffer.pop(0)

        # Уведомляем подписчиков
        for callback in self._log_callbacks:
            try:
                callback(message)
            except Exception:
                pass

    def add_log_callback(self, callback: Callable[[str], None]):
        """Добавить callback для получения логов в реальном времени"""
        self._log_callbacks.append(callback)

    def remove_log_callback(self, callback: Callable[[str], None]):
        """Удалить callback"""
        if callback in self._log_callbacks:
            self._log_callbacks.remove(callback)

    def get_all_logs(self) -> str:
        """Получить все логи из буфера"""
        return "\n".join(self._log_buffer)

    def get_log_file_path(self) -> str:
        """Получить путь к файлу лога"""
        return str(self._log_file)

    def clear_buffer(self):
        """Очистить буфер логов"""
        self._log_buffer.clear()

    def debug(self, message: str):
        """Отладочное сообщение"""
        self._logger.debug(message)

    def info(self, message: str):
        """Информационное сообщение"""
        self._logger.info(message)

    def warning(self, message: str):
        """Предупреждение"""
        self._logger.warning(message)

    def error(self, message: str):
        """Ошибка"""
        self._logger.error(message)

    def exception(self, message: str):
        """Исключение с трейсбеком"""
        self._logger.exception(message)


# Глобальный экземпляр
logger = LoggerService()
