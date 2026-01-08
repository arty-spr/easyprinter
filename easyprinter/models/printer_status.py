"""
Статус принтера
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
from typing import Optional


class PrinterState(Enum):
    """Состояние принтера"""
    UNKNOWN = auto()
    READY = auto()          # Готов
    PRINTING = auto()       # Печатает
    SCANNING = auto()       # Сканирует
    COPYING = auto()        # Копирует
    WARMING = auto()        # Прогревается
    PAPER_JAM = auto()      # Замятие бумаги
    PAPER_OUT = auto()      # Нет бумаги
    TONER_LOW = auto()      # Мало тонера
    ERROR = auto()          # Ошибка
    OFFLINE = auto()        # Не в сети


@dataclass
class PrinterStatus:
    """Статус принтера"""

    # Имя принтера
    printer_name: Optional[str] = None

    # Принтер онлайн
    is_online: bool = False

    # Текущее состояние
    state: PrinterState = PrinterState.UNKNOWN

    # Сообщение о статусе
    status_message: str = ""

    # Уровень тонера (0-100, -1 если неизвестно)
    toner_level: int = -1

    # Количество заданий в очереди печати
    jobs_in_queue: int = 0

    # Поддерживает сканирование
    supports_scanning: bool = True

    # Поддерживает копирование
    supports_copying: bool = True

    # Последнее обновление статуса
    last_updated: datetime = field(default_factory=datetime.now)
