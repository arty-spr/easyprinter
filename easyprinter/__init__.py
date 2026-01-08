"""
EasyPrinter - Приложение для управления принтером HP LaserJet M1536dnf

Порт с C# WPF на Python PyQt6
"""

__version__ = "1.0.0"
__author__ = "EasyPrinter"

from .models import (
    PrintSettings, PaperSize, PaperSource, PrintQuality, DuplexMode, PageOrientation,
    ScanSettings, ScanResolution, ScanFormat, ScanSource,
    PrinterStatus, PrinterState,
    ImageAdjustments
)

from .services import (
    ImageProcessingService,
    StatusService,
    PrinterService,
    ScannerService
)

from .views import (
    MainWindow,
    HomePage,
    PrintView,
    ScanView,
    CopyView,
    StatusView
)

__all__ = [
    # Models
    'PrintSettings', 'PaperSize', 'PaperSource', 'PrintQuality', 'DuplexMode', 'PageOrientation',
    'ScanSettings', 'ScanResolution', 'ScanFormat', 'ScanSource',
    'PrinterStatus', 'PrinterState',
    'ImageAdjustments',

    # Services
    'ImageProcessingService',
    'StatusService',
    'PrinterService',
    'ScannerService',

    # Views
    'MainWindow',
    'HomePage',
    'PrintView',
    'ScanView',
    'CopyView',
    'StatusView'
]
