"""
Сервис звуковых уведомлений
"""

import platform
import subprocess
from .settings_storage import settings_storage


class SoundService:
    """Сервис воспроизведения системных звуков"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def play_success(self) -> None:
        """Воспроизвести звук успеха"""
        if not settings_storage.preferences.sound_enabled:
            return
        self._play_system_sound("success")

    def play_error(self) -> None:
        """Воспроизвести звук ошибки"""
        if not settings_storage.preferences.sound_enabled:
            return
        self._play_system_sound("error")

    def play_notification(self) -> None:
        """Воспроизвести звук уведомления"""
        if not settings_storage.preferences.sound_enabled:
            return
        self._play_system_sound("notification")

    def _play_system_sound(self, sound_type: str) -> None:
        """Воспроизвести системный звук"""
        try:
            system = platform.system()

            if system == "Windows":
                import winsound
                sounds = {
                    "success": winsound.MB_OK,
                    "error": winsound.MB_ICONHAND,
                    "notification": winsound.MB_ICONASTERISK
                }
                winsound.MessageBeep(sounds.get(sound_type, winsound.MB_OK))

            elif system == "Darwin":  # macOS
                sounds = {
                    "success": "Glass",
                    "error": "Basso",
                    "notification": "Ping"
                }
                sound_name = sounds.get(sound_type, "Ping")
                subprocess.run(
                    ["afplay", f"/System/Library/Sounds/{sound_name}.aiff"],
                    capture_output=True,
                    timeout=2
                )

            else:  # Linux
                # Используем paplay если доступен
                sounds = {
                    "success": "/usr/share/sounds/freedesktop/stereo/complete.oga",
                    "error": "/usr/share/sounds/freedesktop/stereo/dialog-error.oga",
                    "notification": "/usr/share/sounds/freedesktop/stereo/message.oga"
                }
                sound_file = sounds.get(sound_type)
                if sound_file:
                    subprocess.run(
                        ["paplay", sound_file],
                        capture_output=True,
                        timeout=2
                    )

        except Exception as e:
            # Молча игнорируем ошибки воспроизведения звука
            pass


# Глобальный экземпляр
sound_service = SoundService()
