"""
Сервис мониторинга статуса принтера
"""

import platform
import subprocess
from datetime import datetime
from typing import Optional, Callable, List
from threading import Timer

from ..models import PrinterStatus, PrinterState


class StatusService:
    """Сервис мониторинга статуса принтера"""

    TARGET_PRINTER_NAME = "HP LaserJet M1536dnf"

    def __init__(self):
        self._timer: Optional[Timer] = None
        self._last_status: PrinterStatus = PrinterStatus()
        self._is_disposed: bool = False
        self._status_changed_callbacks: List[Callable[[PrinterStatus], None]] = []

    def add_status_changed_callback(self, callback: Callable[[PrinterStatus], None]) -> None:
        """Добавить callback для события изменения статуса"""
        self._status_changed_callbacks.append(callback)

    def remove_status_changed_callback(self, callback: Callable[[PrinterStatus], None]) -> None:
        """Удалить callback"""
        if callback in self._status_changed_callbacks:
            self._status_changed_callbacks.remove(callback)

    def _notify_status_changed(self, status: PrinterStatus) -> None:
        """Уведомить всех слушателей об изменении статуса"""
        for callback in self._status_changed_callbacks:
            try:
                callback(status)
            except Exception:
                pass

    def start_monitoring(self) -> None:
        """Запустить мониторинг статуса"""
        self._update_status()
        self._schedule_next_update()

    def stop_monitoring(self) -> None:
        """Остановить мониторинг статуса"""
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule_next_update(self) -> None:
        """Запланировать следующее обновление"""
        if not self._is_disposed:
            self._timer = Timer(5.0, self._timer_callback)
            self._timer.daemon = True
            self._timer.start()

    def _timer_callback(self) -> None:
        """Callback таймера"""
        self._update_status()
        self._schedule_next_update()

    def get_current_status(self) -> PrinterStatus:
        """Получить текущий статус принтера"""
        return self._last_status

    def find_hp_printer(self) -> Optional[str]:
        """Найти HP принтер в системе"""
        try:
            printers = self.get_available_printers()
            for printer in printers:
                if "HP" in printer.upper() and ("1536" in printer or "LASERJET" in printer.upper()):
                    return printer

            # Если конкретный HP не найден, возвращаем первый доступный
            if printers:
                return printers[0]

            return None
        except Exception:
            return None

    def get_available_printers(self) -> List[str]:
        """Получить список доступных принтеров"""
        system = platform.system()
        printers = []

        try:
            if system == "Windows":
                # Скрываем окно PowerShell
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command",
                     "Get-Printer | Select-Object -ExpandProperty Name"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    printers = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]

            elif system == "Darwin":  # macOS
                result = subprocess.run(
                    ["lpstat", "-a"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            # Формат: "printer_name accepting requests..."
                            parts = line.split()
                            if parts:
                                printers.append(parts[0])

            elif system == "Linux":
                result = subprocess.run(
                    ["lpstat", "-a"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split()
                            if parts:
                                printers.append(parts[0])

        except Exception:
            pass

        return printers

    def _update_status(self) -> None:
        """Обновить статус принтера"""
        try:
            printer_name = self.find_hp_printer()

            if printer_name:
                status = PrinterStatus(
                    printer_name=printer_name,
                    is_online=True,
                    state=PrinterState.READY,
                    status_message="Готов к работе",
                    jobs_in_queue=self._get_jobs_count(printer_name),
                    toner_level=self._get_toner_level(printer_name),
                    last_updated=datetime.now()
                )

                # Проверяем реальный статус принтера
                printer_status = self._get_printer_status(printer_name)
                if printer_status:
                    status.state = printer_status['state']
                    status.status_message = printer_status['message']
                    status.is_online = printer_status['is_online']

                self._last_status = status
                self._notify_status_changed(status)

            else:
                self._last_status = PrinterStatus(
                    printer_name=None,
                    is_online=False,
                    state=PrinterState.OFFLINE,
                    status_message="HP принтер не найден",
                    toner_level=-1,
                    last_updated=datetime.now()
                )
                self._notify_status_changed(self._last_status)

        except Exception as e:
            self._last_status = PrinterStatus(
                is_online=False,
                state=PrinterState.ERROR,
                status_message=f"Ошибка: {str(e)}",
                last_updated=datetime.now()
            )
            self._notify_status_changed(self._last_status)

    def _get_printer_status(self, printer_name: str) -> Optional[dict]:
        """Получить детальный статус принтера"""
        system = platform.system()

        try:
            if system == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command",
                     f"Get-Printer -Name '{printer_name}' | Select-Object -ExpandProperty PrinterStatus"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    status_str = result.stdout.strip().lower()
                    return self._parse_windows_status(status_str)

            elif system in ("Darwin", "Linux"):
                result = subprocess.run(
                    ["lpstat", "-p", printer_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return self._parse_unix_status(result.stdout)

        except Exception:
            pass

        return {'state': PrinterState.READY, 'message': "Готов к работе", 'is_online': True}

    def _parse_windows_status(self, status_str: str) -> dict:
        """Парсинг статуса Windows принтера"""
        if "offline" in status_str:
            return {'state': PrinterState.OFFLINE, 'message': "Принтер не в сети", 'is_online': False}
        elif "paperjam" in status_str or "jam" in status_str:
            return {'state': PrinterState.PAPER_JAM, 'message': "Замятие бумаги", 'is_online': True}
        elif "paperout" in status_str or "paper" in status_str and "out" in status_str:
            return {'state': PrinterState.PAPER_OUT, 'message': "Нет бумаги", 'is_online': True}
        elif "toner" in status_str and "low" in status_str:
            return {'state': PrinterState.TONER_LOW, 'message': "Мало тонера", 'is_online': True}
        elif "error" in status_str:
            return {'state': PrinterState.ERROR, 'message': "Ошибка принтера", 'is_online': True}
        elif "printing" in status_str or "busy" in status_str:
            return {'state': PrinterState.PRINTING, 'message': "Идёт печать...", 'is_online': True}
        elif "warmingup" in status_str or "warming" in status_str:
            return {'state': PrinterState.WARMING, 'message': "Прогрев...", 'is_online': True}
        else:
            return {'state': PrinterState.READY, 'message': "Готов к работе", 'is_online': True}

    def _parse_unix_status(self, status_output: str) -> dict:
        """Парсинг статуса Unix/macOS принтера"""
        status_lower = status_output.lower()

        if "disabled" in status_lower or "offline" in status_lower:
            return {'state': PrinterState.OFFLINE, 'message': "Принтер не в сети", 'is_online': False}
        elif "idle" in status_lower:
            return {'state': PrinterState.READY, 'message': "Готов к работе", 'is_online': True}
        elif "printing" in status_lower:
            return {'state': PrinterState.PRINTING, 'message': "Идёт печать...", 'is_online': True}
        else:
            return {'state': PrinterState.READY, 'message': "Готов к работе", 'is_online': True}

    def _get_jobs_count(self, printer_name: str) -> int:
        """Получить количество заданий в очереди"""
        system = platform.system()

        try:
            if system == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-Command",
                     f"(Get-PrintJob -PrinterName '{printer_name}' -ErrorAction SilentlyContinue | Measure-Object).Count"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0 and result.stdout.strip().isdigit():
                    return int(result.stdout.strip())

            elif system in ("Darwin", "Linux"):
                result = subprocess.run(
                    ["lpstat", "-o", printer_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
                    return len(lines)

        except Exception:
            pass

        return 0

    def _get_toner_level(self, printer_name: str) -> int:
        """Получить уровень тонера (примерное значение, т.к. точное получить сложно)"""
        # В реальном приложении можно использовать SNMP для HP принтеров
        # Здесь возвращаем -1 (неизвестно)
        return -1

    def dispose(self) -> None:
        """Освободить ресурсы"""
        if not self._is_disposed:
            self.stop_monitoring()
            self._is_disposed = True
