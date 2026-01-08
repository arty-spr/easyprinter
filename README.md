# EasyPrinter (Python версия)

Приложение для управления принтером HP LaserJet M1536dnf MFP.

Это порт оригинального приложения с C# WPF на Python с использованием PyQt6.

## Возможности

- **Печать** - PDF файлов и изображений (JPG, PNG, BMP, TIFF, GIF)
- **Сканирование** - с возможностью сохранения в PDF, JPEG, PNG, TIFF
- **Копирование** - быстрое копирование документов
- **Мониторинг статуса** - отображение состояния принтера в реальном времени

## Требования

- Python 3.10 или новее
- Windows 10/11, macOS или Linux
- Установленные драйверы принтера HP LaserJet M1536dnf

### Для сканирования

- **Windows**: WIA (Windows Image Acquisition) - встроено в систему
- **macOS/Linux**: SANE (Scanner Access Now Easy) - `brew install sane-backends` или `apt install sane`

## Установка

1. Клонируйте репозиторий или перейдите в папку `python_version`

2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

Или с использованием скрипта:
```bash
# Windows
run.bat

# macOS/Linux
./run.sh
```

## Структура проекта

```
python_version/
├── main.py                 # Точка входа
├── requirements.txt        # Зависимости
├── README.md              # Документация
├── run.bat                # Скрипт запуска (Windows)
├── run.sh                 # Скрипт запуска (Unix)
└── easyprinter/
    ├── __init__.py
    ├── models/            # Модели данных
    │   ├── __init__.py
    │   ├── image_adjustments.py
    │   ├── print_settings.py
    │   ├── printer_status.py
    │   └── scan_settings.py
    ├── services/          # Бизнес-логика
    │   ├── __init__.py
    │   ├── image_processing_service.py
    │   ├── printer_service.py
    │   ├── scanner_service.py
    │   └── status_service.py
    └── views/             # Пользовательский интерфейс
        ├── __init__.py
        ├── styles.py
        ├── main_window.py
        ├── home_page.py
        ├── print_view.py
        ├── scan_view.py
        ├── copy_view.py
        └── status_view.py
```

## Используемые библиотеки

| Библиотека | Назначение |
|-----------|-----------|
| PyQt6 | GUI фреймворк |
| Pillow | Обработка изображений |
| PyMuPDF | Работа с PDF |
| NumPy | Математические операции |

## Отличия от C# версии

- Использует PyQt6 вместо WPF
- Кроссплатформенный (Windows, macOS, Linux)
- Сканирование через WIA (Windows) или SANE (Unix)
- Печать через системные команды (lpr/PowerShell)

## Лицензия

MIT License
