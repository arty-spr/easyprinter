# Продолжение инструкций (Часть 2)

## Шаг 8 (продолжение): print_view.py - окончание файла

Добавить в конец файла `easyprinter/views/print_view.py` (продолжение метода `_on_print_finished`):

```python
            msg.setInformativeText(f"Ошибка: {message}")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    font-size: {Styles.FONT_SIZE_LARGE}px;
                }}
                QMessageBox QLabel {{
                    font-size: {Styles.FONT_SIZE_LARGE}px;
                    min-width: 400px;
                }}
                QPushButton {{
                    font-size: {Styles.FONT_SIZE_NORMAL}px;
                    min-width: 150px;
                    min-height: 50px;
                }}
            """)
            msg.exec()

    def closeEvent(self, event):
        """Очистка ресурсов"""
        if self._pdf_document:
            self._pdf_document.close()
        super().closeEvent(event)
```

---

## Шаг 9: Обновить scan_view.py

Заменить терминологию в файле `easyprinter/views/scan_view.py`.

Найти и заменить следующие строки:

```python
# Было:
DPI_DESCRIPTIONS = {
    150: "Быстро, небольшой размер файла (~0.5 МБ)",
    300: "Стандартное качество для документов (~2 МБ)",
    600: "Высокое качество для фото (~8 МБ)",
    1200: "Максимальное качество, большой файл (~30 МБ)"
}

# Стало:
DPI_DESCRIPTIONS = {
    150: "Быстро, маленький файл",
    300: "Хорошее качество (рекомендуется)",
    600: "Отличное качество для фотографий",
    1200: "Максимальное качество"
}
```

```python
# Было:
self._resolution_combo.addItems([
    "150 DPI - быстро",
    "300 DPI - стандарт",
    "600 DPI - высокое",
    "1200 DPI - максимум"
])

# Стало:
self._resolution_combo.addItems([
    "Быстрое сканирование",
    "Хорошее качество",
    "Высокое качество",
    "Максимальное качество"
])
```

```python
# Было:
self._source_combo.addItems([
    "Стекло сканера",
    "Автоподатчик (АПД)"
])

# Стало:
self._source_combo.addItems([
    "Положить на стекло",
    "Стопка листов сверху"
])
```

```python
# Было:
self._format_combo.addItems([
    "PDF - документ",
    "JPEG - сжатое фото",
    "PNG - без потерь",
    "TIFF - архивный"
])

# Стало:
self._format_combo.addItems([
    "PDF (для документов)",
    "JPEG (для фотографий)",
    "PNG (высокое качество)",
    "TIFF (для архива)"
])
```

Также увеличить размеры кнопок и добавить звуковые уведомления. В методе `_on_save_clicked` после успешного сохранения добавить:

```python
from ..services.sound_service import sound_service

# После строки QMessageBox.information добавить перед ней:
sound_service.play_success()
```

В методе `_on_scan_error` добавить:
```python
sound_service.play_error()
```

---

## Шаг 10: Обновить copy_view.py

В файле `easyprinter/views/copy_view.py` заменить терминологию:

```python
# Было:
self._source_combo.addItems(["Стекло сканера", "Автоподатчик (АПД)"])

# Стало:
self._source_combo.addItems(["Положить на стекло", "Стопка листов сверху"])
```

Добавить импорт и звуковые уведомления:
```python
from ..services.sound_service import sound_service

# В методе _on_finished после QMessageBox.information:
sound_service.play_success()

# После QMessageBox.warning:
sound_service.play_error()
```

---

## Шаг 11: Обновить main_window.py

В файле `easyprinter/views/main_window.py` добавить обработку сигнала быстрой печати.

После строки:
```python
self._home_page.navigate_to_settings.connect(lambda: self._show_page(5))
```

Добавить:
```python
self._home_page.quick_print_file.connect(self._on_quick_print)
```

Добавить новый метод в класс MainWindow:
```python
def _on_quick_print(self, file_path: str):
    """Обработчик быстрой печати с главной страницы"""
    self._show_page(1)  # Переключаемся на страницу печати
    self._print_view.load_file_for_print(file_path)
```

Также увеличить высоту статусной строки:
```python
# Было:
frame.setFixedHeight(50)

# Стало:
frame.setFixedHeight(70)
```

---

## Шаг 12: Обновить services/__init__.py

Добавить новые сервисы в файл `easyprinter/services/__init__.py`:

```python
"""
Сервисы для EasyPrinter
"""

from .image_processing_service import ImageProcessingService
from .status_service import StatusService
from .printer_service import PrinterService
from .scanner_service import ScannerService
from .logger_service import LoggerService, logger
from .update_service import UpdateService
from .settings_storage import SettingsStorage, settings_storage, UserPreferences
from .sound_service import SoundService, sound_service

__all__ = [
    'ImageProcessingService',
    'StatusService',
    'PrinterService',
    'ScannerService',
    'LoggerService',
    'logger',
    'UpdateService',
    'SettingsStorage',
    'settings_storage',
    'UserPreferences',
    'SoundService',
    'sound_service'
]
```

---

## Шаг 13: Обновить views/__init__.py

Добавить новые диалоги в файл `easyprinter/views/__init__.py`:

```python
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
from .file_picker_dialog import FilePickerDialog
from .print_settings_dialog import PrintSettingsDialog
from .print_confirmation_dialog import PrintConfirmationDialog

__all__ = [
    'MainWindow',
    'HomePage',
    'PrintView',
    'ScanView',
    'CopyView',
    'StatusView',
    'SettingsView',
    'Styles',
    'FilePickerDialog',
    'PrintSettingsDialog',
    'PrintConfirmationDialog'
]
```

---

## Шаг 14: Обновить settings_view.py

В файле `easyprinter/views/settings_view.py` добавить переключатель звука.

В методе `_create_about_tab` или создать новую вкладку "Общие настройки":

После строки `tab_widget.addTab(about_tab, "О программе")` добавить:
```python
# Вкладка "Общие"
general_tab = self._create_general_tab()
tab_widget.insertTab(0, general_tab, "Общие")
```

Добавить новый метод:
```python
def _create_general_tab(self) -> QWidget:
    """Создать вкладку общих настроек"""
    from ..services.settings_storage import settings_storage
    
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setSpacing(25)
    layout.setContentsMargins(30, 30, 30, 30)

    # Звуки
    sound_group = QGroupBox("Звуковые уведомления")
    sound_layout = QVBoxLayout(sound_group)

    self._sound_check = QCheckBox("Воспроизводить звуки")
    self._sound_check.setChecked(settings_storage.preferences.sound_enabled)
    self._sound_check.setStyleSheet(f"font-size: {Styles.FONT_SIZE_LARGE}px;")
    self._sound_check.stateChanged.connect(self._on_sound_changed)
    sound_layout.addWidget(self._sound_check)

    sound_hint = QLabel("Звуки помогут понять, что действие выполнено")
    sound_hint.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: {Styles.FONT_SIZE_NORMAL}px;")
    sound_layout.addWidget(sound_hint)

    layout.addWidget(sound_group)
    layout.addStretch()

    return widget

def _on_sound_changed(self, state: int):
    """Обработчик изменения настройки звука"""
    from ..services.settings_storage import settings_storage
    settings_storage.preferences.sound_enabled = (state == Qt.CheckState.Checked.value)
    settings_storage.save()
```

---

## Шаг 15: Создать файл сборки exe

Создать файл `build_exe.py` в корне проекта:

```python
#!/usr/bin/env python3
"""
Скрипт сборки EasyPrinter в exe-файл
"""

import subprocess
import sys
import os
import shutil

def main():
    print("=" * 60)
    print("Сборка EasyPrinter в exe-файл")
    print("=" * 60)

    # Проверяем наличие PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller найден: {PyInstaller.__version__}")
    except ImportError:
        print("Установка PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Путь к главному файлу
    main_file = "main.py"
    if not os.path.exists(main_file):
        print(f"✗ Файл {main_file} не найден!")
        sys.exit(1)

    # Очищаем предыдущие сборки
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Удаление папки {folder}...")
            shutil.rmtree(folder)

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
        "--hidden-import", "fitz",
        "--hidden-import", "numpy",
        
        # Собираем весь пакет easyprinter
        "--collect-all", "easyprinter",
        
        main_file
    ]

    print("\nЗапуск сборки...")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = os.path.join("dist", f"{app_name}.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print()
            print("=" * 60)
            print(f"✓ Сборка успешна!")
            print(f"✓ Файл: {exe_path}")
            print(f"✓ Размер: {size_mb:.1f} МБ")
            print("=" * 60)
        else:
            print("✗ Exe-файл не найден после сборки")
            sys.exit(1)
    else:
        print("✗ Ошибка сборки")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Шаг 16: Обновить requirements.txt

Заменить содержимое файла `requirements.txt`:

```
# EasyPrinter - Зависимости Python

# GUI Framework
PyQt6>=6.5.0

# Работа с изображениями
Pillow>=10.0.0

# Работа с PDF
PyMuPDF>=1.23.0

# Работа с Word документами (DOCX)
python-docx>=1.1.0

# Дополнительные утилиты
numpy>=1.24.0

# Сборка exe
pyinstaller>=6.0.0
```

---

## Шаг 17: Финальная сборка

После внесения всех изменений выполнить:

```bash
# 1. Убедиться что находимся в папке проекта
cd /path/to/easyprinter

# 2. Создать виртуальное окружение (если ещё нет)
python -m venv venv

# 3. Активировать виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Установить зависимости
pip install -r requirements.txt

# 5. Проверить что приложение запускается
python main.py

# 6. Собрать exe
python build_exe.py

# 7. Exe-файл будет в папке dist/EasyPrinter.exe
```

---

## Краткий чеклист изменений

### Новые файлы:
- [ ] `easyprinter/services/settings_storage.py`
- [ ] `easyprinter/services/sound_service.py`
- [ ] `easyprinter/views/file_picker_dialog.py`
- [ ] `easyprinter/views/print_settings_dialog.py`
- [ ] `easyprinter/views/print_confirmation_dialog.py`
- [ ] `build_exe.py`

### Изменённые файлы:
- [ ] `easyprinter/views/styles.py` - увеличены шрифты и контраст
- [ ] `easyprinter/views/home_page.py` - добавлен drag-and-drop
- [ ] `easyprinter/views/print_view.py` - упрощённый интерфейс
- [ ] `easyprinter/views/scan_view.py` - понятная терминология
- [ ] `easyprinter/views/copy_view.py` - понятная терминология
- [ ] `easyprinter/views/main_window.py` - обработка быстрой печати
- [ ] `easyprinter/views/settings_view.py` - настройка звуков
- [ ] `easyprinter/services/__init__.py` - новые сервисы
- [ ] `easyprinter/views/__init__.py` - новые диалоги
- [ ] `requirements.txt` - добавлен pyinstaller

---

## Итоговый результат

После выполнения всех шагов вы получите:

1. **Exe-файл** в папке `dist/EasyPrinter.exe`
2. Приложение с **крупными шрифтами** (18-36px)
3. **Улучшенный контраст** текста
4. **Понятная терминология** без технического жаргона
5. **Drag-and-drop** для быстрой печати
6. **Звуковые уведомления** при успехе/ошибке
7. **Диалог подтверждения** перед печатью
8. **Упрощённый выбор файлов** с недавними документами
9. **Настройки печати** скрыты под кнопку
10. **Сохранение настроек** пользователя между сеансами
