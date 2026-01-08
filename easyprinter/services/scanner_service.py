"""
Сервис сканирования документов
"""

import os
import platform
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, Callable, List
from PIL import Image
from io import BytesIO

from ..models import ScanSettings, ScanFormat, ScanSource, ScanResolution
from .image_processing_service import ImageProcessingService


class ScanProgressEvent:
    """Событие прогресса сканирования"""

    def __init__(self, message: str = "", progress: int = 0):
        self.message = message
        self.progress = progress


class ScanCompletedEvent:
    """Событие завершения сканирования"""

    def __init__(self, success: bool = False, file_path: Optional[str] = None, error: Optional[str] = None):
        self.success = success
        self.file_path = file_path
        self.error = error


class ScannerService:
    """Сервис сканирования документов"""

    def __init__(self, image_processing: ImageProcessingService):
        self._image_processing = image_processing
        self._is_disposed = False
        self._progress_callbacks: List[Callable[[ScanProgressEvent], None]] = []
        self._completed_callbacks: List[Callable[[ScanCompletedEvent], None]] = []

    def add_progress_callback(self, callback: Callable[[ScanProgressEvent], None]) -> None:
        """Добавить callback для события прогресса"""
        self._progress_callbacks.append(callback)

    def add_completed_callback(self, callback: Callable[[ScanCompletedEvent], None]) -> None:
        """Добавить callback для события завершения"""
        self._completed_callbacks.append(callback)

    def _notify_progress(self, message: str, progress: int) -> None:
        """Уведомить о прогрессе"""
        event = ScanProgressEvent(message, progress)
        for callback in self._progress_callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def _notify_completed(self, success: bool, file_path: Optional[str] = None, error: Optional[str] = None) -> None:
        """Уведомить о завершении"""
        event = ScanCompletedEvent(success, file_path, error)
        for callback in self._completed_callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def scan(self, settings: ScanSettings) -> Optional[Image.Image]:
        """Выполнить сканирование"""
        try:
            self._notify_progress("Поиск сканера...", 10)

            system = platform.system()

            if system == "Windows":
                image = self._scan_windows(settings)
            elif system == "Darwin":
                image = self._scan_macos(settings)
            else:
                image = self._scan_linux(settings)

            if image is None:
                raise RuntimeError("Не удалось получить изображение от сканера")

            self._notify_progress("Обработка изображения...", 70)

            # Применяем настройки изображения если есть
            if settings.image_adjustments.has_changes:
                image = self._image_processing.apply_adjustments(image, settings.image_adjustments)

            self._notify_progress("Сканирование завершено", 100)

            return image

        except Exception as e:
            self._notify_completed(False, error=str(e))
            raise

    def _scan_windows(self, settings: ScanSettings) -> Optional[Image.Image]:
        """Сканирование на Windows через WIA"""
        self._notify_progress("Запуск сканирования (Windows WIA)...", 30)

        # Создаём временный файл для сохранения скана
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # PowerShell скрипт для сканирования через WIA
            dpi = settings.resolution.value
            ps_script = f'''
Add-Type -AssemblyName System.Drawing

$deviceManager = New-Object -ComObject WIA.DeviceManager
$device = $null

foreach ($d in $deviceManager.DeviceInfos) {{
    if ($d.Type -eq 1) {{  # Scanner
        $device = $d.Connect()
        break
    }}
}}

if ($device -eq $null) {{
    Write-Error "Сканер не найден"
    exit 1
}}

$item = $device.Items[1]

# Настройки разрешения
$item.Properties["6146"].Value = 2  # Color
$item.Properties["6147"].Value = {dpi}  # Horizontal DPI
$item.Properties["6148"].Value = {dpi}  # Vertical DPI

# Сканирование
$imageFile = $item.Transfer()
$imageFile.SaveFile("{tmp_path.replace(chr(92), chr(92)+chr(92))}")
'''

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0 or not os.path.exists(tmp_path):
                # Если WIA не сработал, пробуем через wiaaut.dll
                return self._scan_windows_fallback(settings)

            return Image.open(tmp_path)

        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

    def _scan_windows_fallback(self, settings: ScanSettings) -> Optional[Image.Image]:
        """Запасной метод сканирования на Windows"""
        # Открываем стандартное приложение сканирования Windows
        subprocess.run(["start", "ms-screenclip:"], shell=True, timeout=5)
        raise RuntimeError("Автоматическое сканирование недоступно. Используйте стандартное приложение Windows для сканирования.")

    def _scan_macos(self, settings: ScanSettings) -> Optional[Image.Image]:
        """Сканирование на macOS через Image Capture / SANE"""
        self._notify_progress("Запуск сканирования (macOS)...", 30)

        # Используем sane-backends если установлен
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            dpi = settings.resolution.value
            mode = "Color"

            # Пробуем scanimage (SANE)
            args = [
                "scanimage",
                f"--resolution={dpi}",
                f"--mode={mode}",
                f"--format=png",
                f"-o", tmp_path
            ]

            if settings.source == ScanSource.ADF:
                args.append("--source=ADF")

            result = subprocess.run(args, capture_output=True, text=True, timeout=120)

            if result.returncode == 0 and os.path.exists(tmp_path):
                return Image.open(tmp_path)
            else:
                # Открываем Image Capture
                subprocess.run(["open", "-a", "Image Capture"], timeout=5)
                raise RuntimeError("Автоматическое сканирование недоступно. Используйте Image Capture для сканирования.")

        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

    def _scan_linux(self, settings: ScanSettings) -> Optional[Image.Image]:
        """Сканирование на Linux через SANE"""
        self._notify_progress("Запуск сканирования (Linux SANE)...", 30)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            dpi = settings.resolution.value

            args = [
                "scanimage",
                f"--resolution={dpi}",
                "--mode=Color",
                "--format=png",
                "-o", tmp_path
            ]

            if settings.source == ScanSource.ADF:
                args.append("--source=ADF")

            result = subprocess.run(args, capture_output=True, text=True, timeout=120)

            if result.returncode == 0 and os.path.exists(tmp_path):
                return Image.open(tmp_path)
            else:
                raise RuntimeError(f"Ошибка сканирования: {result.stderr}")

        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

    def save_scan(self, image: Image.Image, settings: ScanSettings) -> str:
        """Сохранить отсканированное изображение"""
        output_path = settings.get_full_path()

        # Создаём директорию если не существует
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        if settings.format == ScanFormat.PDF:
            self._save_as_pdf(image, output_path)
        elif settings.format == ScanFormat.JPEG:
            # Конвертируем в RGB если есть альфа-канал
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            image.save(output_path, 'JPEG', quality=95)
        elif settings.format == ScanFormat.PNG:
            image.save(output_path, 'PNG')
        elif settings.format == ScanFormat.TIFF:
            image.save(output_path, 'TIFF')

        self._notify_completed(True, output_path)
        return output_path

    def _save_as_pdf(self, image: Image.Image, output_path: str) -> None:
        """Сохранить изображение как PDF"""
        # Конвертируем в RGB если нужно
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        image.save(output_path, 'PDF', resolution=100.0)

    def get_available_scanners(self) -> List[str]:
        """Получить список доступных сканеров"""
        system = platform.system()
        scanners = []

        try:
            if system == "Windows":
                # Используем WIA для получения списка сканеров
                ps_script = '''
$deviceManager = New-Object -ComObject WIA.DeviceManager
foreach ($d in $deviceManager.DeviceInfos) {
    if ($d.Type -eq 1) {
        Write-Output $d.Properties["Name"].Value
    }
}
'''
                result = subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    scanners = [s.strip() for s in result.stdout.strip().split('\n') if s.strip()]

            elif system in ("Darwin", "Linux"):
                # Используем SANE
                result = subprocess.run(
                    ["scanimage", "-L"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            # Формат: device `name' is a Vendor Model Type
                            if '`' in line and "'" in line:
                                start = line.index('`') + 1
                                end = line.index("'")
                                scanners.append(line[start:end])

        except Exception:
            pass

        return scanners

    def dispose(self) -> None:
        """Освободить ресурсы"""
        self._is_disposed = True
        self._progress_callbacks.clear()
        self._completed_callbacks.clear()
