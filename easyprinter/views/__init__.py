"""
Представления (GUI) для EasyPrinter
"""

from .main_window import MainWindow
from .home_page import HomePage
from .print_view import PrintView
from .scan_view import ScanView
from .copy_view import CopyView
from .status_view import StatusView
from .settings_view import SettingsView
from .styles import Styles

__all__ = [
    'MainWindow',
    'HomePage',
    'PrintView',
    'ScanView',
    'CopyView',
    'StatusView',
    'SettingsView',
    'Styles'
]
