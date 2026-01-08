"""
Настройки сканирования
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import os

from .image_adjustments import ImageAdjustments


class ScanResolution(Enum):
    """Разрешение сканирования (DPI)"""
    DPI_150 = 150
    DPI_300 = 300
    DPI_600 = 600
    DPI_1200 = 1200


class ScanFormat(Enum):
    """Формат сохранения"""
    PDF = "pdf"
    JPEG = "jpg"
    PNG = "png"
    TIFF = "tiff"


class ScanSource(Enum):
    """Источник сканирования"""
    FLATBED = "flatbed"     # Стекло сканера
    ADF = "adf"             # Автоподатчик документов


@dataclass
class ScanSettings:
    """Настройки сканирования"""

    # Разрешение сканирования (DPI)
    resolution: ScanResolution = ScanResolution.DPI_300

    # Формат сохранения
    format: ScanFormat = ScanFormat.PDF

    # Папка для сохранения
    output_folder: str = field(default_factory=lambda: str(Path.home() / "Documents"))

    # Имя файла (без расширения)
    file_name: str = field(default_factory=lambda: f"Скан_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    # Источник сканирования
    source: ScanSource = ScanSource.FLATBED

    # Настройки изображения
    image_adjustments: ImageAdjustments = field(default_factory=ImageAdjustments)

    def get_full_path(self) -> str:
        """Получить полный путь к файлу"""
        extension = self.format.value
        return os.path.join(self.output_folder, f"{self.file_name}.{extension}")
