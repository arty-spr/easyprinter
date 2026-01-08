# Инструкции для Claude Code: Улучшение EasyPrinter для пожилых

## Цель
Модифицировать приложение EasyPrinter для удобного использования пожилыми людьми и собрать exe-файл.

---

## Структура архива

```
easyprinter_update/
├── README.md                    # Этот файл
├── build_exe.py                 # Скрипт сборки exe
├── CLAUDE_CODE_INSTRUCTIONS_PART2.md  # Детальные инструкции
└── easyprinter/
    ├── services/
    │   ├── settings_storage.py  # НОВЫЙ: хранение настроек
    │   └── sound_service.py     # НОВЫЙ: звуковые уведомления
    └── views/
        ├── styles.py            # ЗАМЕНИТЬ: увеличенные шрифты
        ├── file_picker_dialog.py      # НОВЫЙ: упрощённый выбор файлов
        ├── print_confirmation_dialog.py # НОВЫЙ: подтверждение печати
        └── print_settings_dialog.py   # НОВЫЙ: настройки печати
```

---

## Быстрый старт для Claude Code

### 1. Скопировать готовые файлы

Скопировать все файлы из архива в соответствующие папки проекта:

```bash
# Новые сервисы
cp easyprinter_update/easyprinter/services/settings_storage.py easyprinter/services/
cp easyprinter_update/easyprinter/services/sound_service.py easyprinter/services/

# Новые и обновлённые views
cp easyprinter_update/easyprinter/views/styles.py easyprinter/views/
cp easyprinter_update/easyprinter/views/file_picker_dialog.py easyprinter/views/
cp easyprinter_update/easyprinter/views/print_confirmation_dialog.py easyprinter/views/
cp easyprinter_update/easyprinter/views/print_settings_dialog.py easyprinter/views/

# Скрипт сборки
cp easyprinter_update/build_exe.py ./
```

### 2. Обновить easyprinter/services/__init__.py

Добавить импорты новых сервисов:

```python
from .settings_storage import SettingsStorage, settings_storage, UserPreferences
from .sound_service import SoundService, sound_service

__all__ = [
    # ... существующие экспорты ...
    'SettingsStorage',
    'settings_storage',
    'UserPreferences',
    'SoundService',
    'sound_service'
]
```

### 3. Обновить easyprinter/views/__init__.py

Добавить импорты новых диалогов:

```python
from .file_picker_dialog import FilePickerDialog
from .print_settings_dialog import PrintSettingsDialog
from .print_confirmation_dialog import PrintConfirmationDialog

__all__ = [
    # ... существующие экспорты ...
    'FilePickerDialog',
    'PrintSettingsDialog',
    'PrintConfirmationDialog'
]
```

### 4. Обновить home_page.py

Заменить содержимое файла `easyprinter/views/home_page.py`:

```python
"""
Главная страница приложения с поддержкой drag-and-drop
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from .styles import Styles


class DropZone(QFrame):
    """Зона для перетаскивания файлов"""

    file_dropped = pyqtSignal(str)

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._is_drag_over = False
        self._update_style()
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 80px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel("Перетащите файл сюда\\nдля быстрой печати")
        text_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_LARGE}px;
            color: {Styles.TEXT_SECONDARY};
            background: transparent;
        """)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        hint_label = QLabel("PDF, Word, изображения")
        hint_label.setStyleSheet(f"""
            font-size: {Styles.FONT_SIZE_NORMAL}px;
            color: {Styles.TEXT_SECONDARY};
            background: transparent;
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

    def _update_style(self):
        self.setStyleSheet(Styles.get_drop_zone_style(self._is_drag_over))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self._is_drag_over = True
                    self._update_style()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._is_drag_over = False
        self._update_style()

    def dropEvent(self, event: QDropEvent):
        self._is_drag_over = False
        self._update_style()
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self.file_dropped.emit(file_path)
                    return
        event.ignore()


class HomePage(QWidget):
    """Главная страница с навигацией"""

    navigate_to_print = pyqtSignal()
    navigate_to_scan = pyqtSignal()
    navigate_to_copy = pyqtSignal()
    navigate_to_status = pyqtSignal()
    navigate_to_settings = pyqtSignal()
    quick_print_file = pyqtSignal(str)  # Новый сигнал

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 30)

        # Заголовок
        title_label = QLabel("EasyPrinter")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(Styles.FONT_SIZE_TITLE + 12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {Styles.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        subtitle_label = QLabel("Простая печать и сканирование")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: {Styles.FONT_SIZE_LARGE}px;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # Зона перетаскивания
        drop_zone = DropZone()
        drop_zone.setFixedSize(500, 200)
        drop_zone.file_dropped.connect(self.quick_print_file.emit)
        layout.addWidget(drop_zone, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(30)

        # Навигационные кнопки
        nav_grid = QGridLayout()
        nav_grid.setSpacing(25)

        print_btn = self._create_nav_button("🖨️\\nПЕЧАТЬ", Styles.PRIMARY_COLOR, self.navigate_to_print.emit)
        nav_grid.addWidget(print_btn, 0, 0)

        scan_btn = self._create_nav_button("📷\\nСКАН", Styles.SUCCESS_COLOR, self.navigate_to_scan.emit)
        nav_grid.addWidget(scan_btn, 0, 1)

        copy_btn = self._create_nav_button("📋\\nКОПИЯ", Styles.WARNING_COLOR, self.navigate_to_copy.emit)
        nav_grid.addWidget(copy_btn, 1, 0)

        status_btn = self._create_nav_button("📊\\nСТАТУС", Styles.PURPLE_COLOR, self.navigate_to_status.emit)
        nav_grid.addWidget(status_btn, 1, 1)

        nav_container = QWidget()
        nav_container.setLayout(nav_grid)
        layout.addWidget(nav_container, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(20)

        # Кнопка настроек
        settings_btn = QPushButton("⚙️  Настройки")
        settings_btn.setFixedSize(250, 70)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Styles.TEXT_SECONDARY};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #5a6268; }}
        """)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self.navigate_to_settings.emit)
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    def _create_nav_button(self, text: str, color: str, callback) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(220, 180)
        btn.setStyleSheet(Styles.get_nav_button_style(color))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn
```

### 5. Обновить main_window.py

В методе `_init_ui` после строки:
```python
self._home_page.navigate_to_settings.connect(lambda: self._show_page(5))
```

Добавить:
```python
self._home_page.quick_print_file.connect(self._on_quick_print)
```

Добавить новый метод в класс:
```python
def _on_quick_print(self, file_path: str):
    """Обработчик быстрой печати"""
    self._show_page(1)
    self._print_view.load_file_for_print(file_path)
```

Изменить высоту статусной строки:
```python
frame.setFixedHeight(70)  # Было 50
```

### 6. Обновить print_view.py

Это самое большое изменение. Нужно:
1. Убрать все настройки из основного интерфейса
2. Добавить кнопку "Настройки печати" которая открывает диалог
3. Добавить диалог подтверждения перед печатью
4. Добавить звуки
5. Добавить метод `load_file_for_print()`

Смотри полный код в файле CLAUDE_CODE_INSTRUCTIONS_PART2.md

### 7. Обновить scan_view.py

Заменить технические термины:

```python
# Разрешение
self._resolution_combo.addItems([
    "Быстрое сканирование",
    "Хорошее качество", 
    "Высокое качество",
    "Максимальное качество"
])

# Источник
self._source_combo.addItems([
    "Положить на стекло",
    "Стопка листов сверху"
])

# Формат
self._format_combo.addItems([
    "PDF (для документов)",
    "JPEG (для фотографий)",
    "PNG (высокое качество)",
    "TIFF (для архива)"
])
```

Добавить импорт и звуки:
```python
from ..services.sound_service import sound_service

# После успешного сохранения:
sound_service.play_success()

# После ошибки:
sound_service.play_error()
```

### 8. Обновить copy_view.py

Аналогично заменить термины и добавить звуки.

### 9. Обновить requirements.txt

Добавить в конец:
```
pyinstaller>=6.0.0
```

### 10. Собрать exe

```bash
pip install -r requirements.txt
python main.py  # Проверить что работает
python build_exe.py
```

Exe-файл появится в `dist/EasyPrinter.exe`

---

## Итоговые изменения

| Что изменено | Зачем |
|-------------|-------|
| Шрифты 18-36px | Легче читать |
| Контраст текста | Лучше видно |
| Drag-and-drop | Быстрая печать |
| Понятные термины | Нет технического жаргона |
| Звуковые уведомления | Понятно что произошло |
| Диалог подтверждения | Защита от ошибок |
| Упрощённый выбор файлов | Недавние файлы, быстрый доступ |
| Кнопка "Настройки печати" | Настройки отдельно, не мешают |
| Сохранение настроек | Запоминает предпочтения |

---

## Проверка после изменений

1. Запустить `python main.py`
2. Проверить что:
   - Шрифты крупные и читаемые
   - Можно перетащить файл на главную страницу
   - При печати появляется подтверждение
   - Звуки воспроизводятся
   - Настройки открываются по кнопке
   - Недавние файлы сохраняются
3. Собрать exe и проверить что он работает
