#!/usr/bin/env python3
"""
Скрипт сборки EasyPrinter в exe-файл

Использование:
    python build_exe.py
"""

import subprocess
import sys
import os
import shutil


def main():
    print("=" * 60)
    print("       Сборка EasyPrinter в exe-файл")
    print("=" * 60)
    print()

    # Проверяем наличие PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller найден: версия {PyInstaller.__version__}")
    except ImportError:
        print("⚙ Установка PyInstaller...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            capture_output=True
        )
        if result.returncode != 0:
            print("✗ Не удалось установить PyInstaller")
            sys.exit(1)
        print("✓ PyInstaller установлен")

    # Путь к главному файлу
    main_file = "main.py"
    if not os.path.exists(main_file):
        print(f"✗ Файл {main_file} не найден!")
        print("  Убедитесь, что запускаете скрипт из папки проекта")
        sys.exit(1)

    print(f"✓ Найден главный файл: {main_file}")

    # Очищаем предыдущие сборки
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"⚙ Удаление папки {folder}...")
            shutil.rmtree(folder)

    # Удаляем старый spec файл
    spec_file = "EasyPrinter.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # Параметры сборки
    app_name = "EasyPrinter"
    
    # Команда PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", app_name,
        "--onefile",           # Один exe-файл
        "--windowed",          # Без консольного окна
        "--noconfirm",         # Без подтверждений
        "--clean",             # Чистая сборка
        
        # Добавляем все необходимые модули
        "--hidden-import", "PyQt6",
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtGui",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageEnhance",
        "--hidden-import", "PIL.ImageFilter",
        "--hidden-import", "fitz",
        "--hidden-import", "numpy",
        
        # Собираем весь пакет easyprinter
        "--collect-all", "easyprinter",
        
        main_file
    ]

    print()
    print("⚙ Запуск сборки...")
    print("  Это может занять несколько минут...")
    print()

    result = subprocess.run(cmd)

    print()

    if result.returncode == 0:
        exe_path = os.path.join("dist", f"{app_name}.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print("=" * 60)
            print("              СБОРКА УСПЕШНА!")
            print("=" * 60)
            print()
            print(f"  📁 Файл: {os.path.abspath(exe_path)}")
            print(f"  📊 Размер: {size_mb:.1f} МБ")
            print()
            print("  Теперь вы можете:")
            print("  1. Скопировать exe-файл в любую папку")
            print("  2. Создать ярлык на рабочем столе")
            print("  3. Запустить программу двойным кликом")
            print()
            print("=" * 60)
        else:
            print("✗ Exe-файл не найден после сборки")
            sys.exit(1)
    else:
        print("=" * 60)
        print("              ОШИБКА СБОРКИ")
        print("=" * 60)
        print()
        print("  Возможные причины:")
        print("  - Не установлены все зависимости")
        print("  - Ошибки в коде Python")
        print("  - Недостаточно памяти")
        print()
        print("  Попробуйте:")
        print("  1. pip install -r requirements.txt")
        print("  2. python main.py (проверить что запускается)")
        print("  3. Запустить сборку снова")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
