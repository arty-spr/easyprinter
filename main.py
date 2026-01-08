#!/usr/bin/env python3
"""
EasyPrinter - Главный файл приложения

Приложение для управления принтером HP LaserJet M1536dnf MFP
Функции: печать, сканирование, копирование, мониторинг статуса
"""

import sys
import locale
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLocale
from PyQt6.QtGui import QFont

from easyprinter.views import MainWindow


def main():
    """Точка входа в приложение"""
    # Устанавливаем русскую локаль
    try:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
        except locale.Error:
            pass  # Используем системную локаль

    # Создаём приложение
    app = QApplication(sys.argv)

    # Устанавливаем локаль Qt
    QLocale.setDefault(QLocale(QLocale.Language.Russian, QLocale.Country.Russia))

    # Устанавливаем шрифт по умолчанию
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)

    # Устанавливаем имя приложения
    app.setApplicationName("EasyPrinter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("EasyPrinter")

    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()

    # Запускаем цикл обработки событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
