"""
Сервис печати документов
"""

import os
import platform
import subprocess
import tempfile
from typing import Optional, Tuple
from PIL import Image

from ..models import PrintSettings, PaperSize, PageOrientation
from .status_service import StatusService
from .image_processing_service import ImageProcessingService


class PrinterService:
    """Сервис печати документов"""

    def __init__(self, status_service: StatusService, image_processing: ImageProcessingService):
        self._status_service = status_service
        self._image_processing = image_processing

    def print_pdf(self, file_path: str, settings: PrintSettings) -> None:
        """Печать PDF файла"""
        printer = self._status_service.find_hp_printer()
        if not printer:
            raise RuntimeError("HP принтер не найден")

        system = platform.system()

        if system == "Windows":
            self._print_pdf_windows(file_path, printer, settings)
        elif system == "Darwin":
            self._print_pdf_macos(file_path, printer, settings)
        else:
            self._print_pdf_linux(file_path, printer, settings)

    def _print_pdf_windows(self, file_path: str, printer: str, settings: PrintSettings) -> None:
        """Печать PDF на Windows"""
        import sys

        # Скрываем окно PowerShell
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        # Используем win32api для печати напрямую если доступно
        try:
            import win32api
            import win32print

            # Устанавливаем принтер по умолчанию временно
            win32print.SetDefaultPrinter(printer)

            # Печатаем файл
            for _ in range(settings.copies):
                win32api.ShellExecute(0, "print", file_path, None, ".", 0)
            return
        except ImportError:
            pass  # win32api не установлен, используем PowerShell

        # Fallback: PowerShell со скрытым окном
        ps_command = f'''
$file = "{file_path.replace(chr(92), chr(92)+chr(92))}"
Start-Process -FilePath $file -Verb Print -WindowStyle Hidden
Start-Sleep -Seconds 3
'''

        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps_command],
            startupinfo=startupinfo,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def _print_pdf_macos(self, file_path: str, printer: str, settings: PrintSettings) -> None:
        """Печать PDF на macOS"""
        args = ["lpr", "-P", printer]

        # Количество копий
        if settings.copies > 1:
            args.extend(["-#", str(settings.copies)])

        # Ориентация
        if settings.orientation == PageOrientation.LANDSCAPE:
            args.extend(["-o", "landscape"])

        # Диапазон страниц
        if settings.page_range:
            page_from, page_to = self._parse_page_range(settings.page_range)
            args.extend(["-o", f"page-ranges={page_from}-{page_to}"])

        args.append(file_path)
        subprocess.run(args, timeout=60)

    def _print_pdf_linux(self, file_path: str, printer: str, settings: PrintSettings) -> None:
        """Печать PDF на Linux"""
        args = ["lpr", "-P", printer]

        if settings.copies > 1:
            args.extend(["-#", str(settings.copies)])

        if settings.orientation == PageOrientation.LANDSCAPE:
            args.extend(["-o", "landscape"])

        if settings.page_range:
            page_from, page_to = self._parse_page_range(settings.page_range)
            args.extend(["-o", f"page-ranges={page_from}-{page_to}"])

        args.append(file_path)
        subprocess.run(args, timeout=60)

    def print_image(self, file_path: str, settings: PrintSettings) -> None:
        """Печать изображения"""
        printer = self._status_service.find_hp_printer()
        if not printer:
            raise RuntimeError("HP принтер не найден")

        # Открываем и обрабатываем изображение
        image = Image.open(file_path)

        # Применяем настройки изображения если есть изменения
        if settings.image_adjustments.has_changes:
            image = self._image_processing.apply_adjustments(image, settings.image_adjustments)

        # Применяем масштаб
        if settings.scale != 100:
            new_width = int(image.width * settings.scale / 100)
            new_height = int(image.height * settings.scale / 100)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            image.save(tmp_path, 'PNG')

        try:
            system = platform.system()

            if system == "Windows":
                self._print_image_windows(tmp_path, printer, settings)
            elif system == "Darwin":
                self._print_image_macos(tmp_path, printer, settings)
            else:
                self._print_image_linux(tmp_path, printer, settings)
        finally:
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _print_image_windows(self, file_path: str, printer: str, settings: PrintSettings) -> None:
        """Печать изображения на Windows"""
        # Скрываем окно
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        # Пробуем win32api если доступен
        try:
            import win32api
            import win32print

            win32print.SetDefaultPrinter(printer)
            for _ in range(settings.copies):
                win32api.ShellExecute(0, "print", file_path, None, ".", 0)
            return
        except ImportError:
            pass

        # Fallback: через rundll32 (без окна)
        for _ in range(settings.copies):
            subprocess.run(
                ["rundll32", "shimgvw.dll,ImageView_PrintTo", f"/pt", file_path, printer],
                startupinfo=startupinfo,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

    def _print_image_macos(self, file_path: str, printer: str, settings: PrintSettings) -> None:
        """Печать изображения на macOS"""
        args = ["lpr", "-P", printer]

        if settings.copies > 1:
            args.extend(["-#", str(settings.copies)])

        if settings.orientation == PageOrientation.LANDSCAPE:
            args.extend(["-o", "landscape"])

        # Подгонка под размер страницы
        args.extend(["-o", "fit-to-page"])

        args.append(file_path)
        subprocess.run(args, timeout=60)

    def _print_image_linux(self, file_path: str, printer: str, settings: PrintSettings) -> None:
        """Печать изображения на Linux"""
        args = ["lpr", "-P", printer]

        if settings.copies > 1:
            args.extend(["-#", str(settings.copies)])

        if settings.orientation == PageOrientation.LANDSCAPE:
            args.extend(["-o", "landscape"])

        args.extend(["-o", "fit-to-page"])

        args.append(file_path)
        subprocess.run(args, timeout=60)

    def print_file(self, file_path: str, settings: PrintSettings) -> None:
        """Печать документа (определяет тип по расширению)"""
        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".pdf":
            self.print_pdf(file_path, settings)
        elif extension in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif"):
            self.print_image(file_path, settings)
        else:
            raise ValueError(f"Формат файла {extension} не поддерживается")

    def get_available_printers(self) -> list:
        """Получить список доступных принтеров"""
        return self._status_service.get_available_printers()

    def _parse_page_range(self, range_str: str) -> Tuple[int, int]:
        """Парсинг диапазона страниц"""
        if '-' in range_str:
            parts = range_str.split('-')
            if len(parts) == 2:
                try:
                    return int(parts[0].strip()), int(parts[1].strip())
                except ValueError:
                    pass
        else:
            try:
                page = int(range_str.strip())
                return page, page
            except ValueError:
                pass

        return 1, 9999

    def get_paper_size_name(self, paper_size: PaperSize) -> str:
        """Получить системное название размера бумаги"""
        mapping = {
            PaperSize.A4: "A4",
            PaperSize.LETTER: "Letter",
            PaperSize.LEGAL: "Legal",
            PaperSize.A5: "A5",
            PaperSize.ENVELOPE_10: "Env10",
            PaperSize.ENVELOPE_C5: "EnvC5",
            PaperSize.ENVELOPE_DL: "EnvDL"
        }
        return mapping.get(paper_size, "A4")
