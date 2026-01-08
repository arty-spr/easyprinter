"""
Модели данных для EasyPrinter
"""

from .print_settings import PrintSettings, PaperSize, PaperSource, PrintQuality, DuplexMode, PageOrientation
from .scan_settings import ScanSettings, ScanResolution, ScanFormat, ScanSource
from .printer_status import PrinterStatus, PrinterState
from .image_adjustments import ImageAdjustments

__all__ = [
    'PrintSettings', 'PaperSize', 'PaperSource', 'PrintQuality', 'DuplexMode', 'PageOrientation',
    'ScanSettings', 'ScanResolution', 'ScanFormat', 'ScanSource',
    'PrinterStatus', 'PrinterState',
    'ImageAdjustments'
]
