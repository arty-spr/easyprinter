"""
Сервис хранения пользовательских настроек
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class UserPreferences:
    """Пользовательские настройки"""
    # Последние пути
    last_print_folder: str = ""
    last_scan_folder: str = ""
    recent_files: list = field(default_factory=list)  # Последние 10 файлов

    # Настройки печати по умолчанию
    default_copies: int = 1
    default_paper_size: int = 0  # Индекс в комбобоксе
    default_quality: int = 1

    # Настройки сканирования
    default_scan_resolution: int = 1
    default_scan_format: int = 0

    # Звуки
    sound_enabled: bool = True


class SettingsStorage:
    """Хранилище настроек пользователя"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._settings_dir = Path.home() / ".easyprinter"
        self._settings_file = self._settings_dir / "preferences.json"
        self._settings_dir.mkdir(parents=True, exist_ok=True)

        self._preferences = self._load()

    def _load(self) -> UserPreferences:
        """Загрузить настройки из файла"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Фильтруем только известные поля
                    known_fields = {f.name for f in UserPreferences.__dataclass_fields__.values()}
                    filtered_data = {k: v for k, v in data.items() if k in known_fields}
                    return UserPreferences(**filtered_data)
        except Exception as e:
            print(f"Не удалось загрузить настройки: {e}")

        return UserPreferences()

    def save(self) -> None:
        """Сохранить настройки в файл"""
        try:
            data = asdict(self._preferences)
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Не удалось сохранить настройки: {e}")

    @property
    def preferences(self) -> UserPreferences:
        return self._preferences

    def add_recent_file(self, file_path: str) -> None:
        """Добавить файл в список недавних"""
        if not file_path:
            return

        # Удаляем если уже есть
        if file_path in self._preferences.recent_files:
            self._preferences.recent_files.remove(file_path)

        # Добавляем в начало
        self._preferences.recent_files.insert(0, file_path)

        # Оставляем только 10 последних
        self._preferences.recent_files = self._preferences.recent_files[:10]

        # Обновляем папку
        folder = os.path.dirname(file_path)
        if folder:
            self._preferences.last_print_folder = folder

        self.save()

    def get_recent_files(self) -> list:
        """Получить список недавних файлов (только существующие)"""
        existing = []
        for f in self._preferences.recent_files:
            if os.path.exists(f):
                existing.append(f)
        return existing


# Глобальный экземпляр
settings_storage = SettingsStorage()
