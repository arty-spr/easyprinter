"""
Настройки печати
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from .image_adjustments import ImageAdjustments


class PaperSize(Enum):
    """Размер бумаги"""
    A4 = auto()
    LETTER = auto()
    LEGAL = auto()
    A5 = auto()
    ENVELOPE_10 = auto()
    ENVELOPE_C5 = auto()
    ENVELOPE_DL = auto()


class PaperSource(Enum):
    """Источник бумаги"""
    AUTO = auto()
    TRAY1 = auto()
    MANUAL_FEED = auto()


class PrintQuality(Enum):
    """Качество печати"""
    DRAFT = auto()      # Черновик (600dpi)
    NORMAL = auto()     # Нормальное
    HIGH = auto()       # Высокое (FastRes 1200)


class DuplexMode(Enum):
    """Режим двусторонней печати"""
    NONE = auto()           # Односторонняя
    MANUAL_DUPLEX = auto()  # Ручной дуплекс


class PageOrientation(Enum):
    """Ориентация страницы"""
    PORTRAIT = auto()   # Книжная
    LANDSCAPE = auto()  # Альбомная


@dataclass
class PrintSettings:
    """Настройки печати"""

    # Количество копий (1-99)
    copies: int = 1

    # Размер бумаги
    paper_size: PaperSize = PaperSize.A4

    # Источник бумаги
    paper_source: PaperSource = PaperSource.AUTO

    # Качество печати
    quality: PrintQuality = PrintQuality.NORMAL

    # Двусторонняя печать
    duplex: DuplexMode = DuplexMode.NONE

    # Диапазон страниц (None = все страницы)
    page_range: Optional[str] = None

    # Страниц на листе
    pages_per_sheet: int = 1

    # Масштаб (25-400%)
    scale: int = 100

    # Ориентация
    orientation: PageOrientation = PageOrientation.PORTRAIT

    # Настройки изображения
    image_adjustments: ImageAdjustments = field(default_factory=ImageAdjustments)
