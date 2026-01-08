"""
Сервис обновления из Git
"""

import subprocess
import os
from typing import Tuple, Optional
from .logger_service import logger


class UpdateService:
    """Сервис для обновления приложения из Git"""

    def __init__(self, repo_path: Optional[str] = None):
        if repo_path:
            self._repo_path = repo_path
        else:
            # Определяем путь к репозиторию относительно текущего файла
            self._repo_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def check_for_updates(self) -> Tuple[bool, str]:
        """
        Проверить наличие обновлений

        Returns:
            (has_updates, message)
        """
        try:
            logger.info("Проверка обновлений...")

            # Получаем информацию с удалённого репозитория
            result = subprocess.run(
                ["git", "fetch"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Ошибка fetch: {result.stderr}")
                return False, f"Ошибка проверки: {result.stderr}"

            # Сравниваем локальную и удалённую ветки
            result = subprocess.run(
                ["git", "status", "-uno"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout.lower()

            if "your branch is behind" in output:
                logger.info("Найдены обновления")
                return True, "Доступны обновления"
            elif "your branch is up to date" in output:
                logger.info("Обновлений нет")
                return False, "У вас последняя версия"
            else:
                return False, "Не удалось определить статус"

        except subprocess.TimeoutExpired:
            logger.error("Таймаут при проверке обновлений")
            return False, "Таймаут при проверке обновлений"
        except FileNotFoundError:
            logger.error("Git не установлен")
            return False, "Git не установлен в системе"
        except Exception as e:
            logger.exception(f"Ошибка проверки обновлений: {e}")
            return False, f"Ошибка: {str(e)}"

    def update(self) -> Tuple[bool, str]:
        """
        Выполнить обновление

        Returns:
            (success, message)
        """
        try:
            logger.info("Начало обновления...")

            # Сохраняем локальные изменения (если есть)
            subprocess.run(
                ["git", "stash"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Получаем обновления
            result = subprocess.run(
                ["git", "pull", "--rebase"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"Ошибка pull: {result.stderr}")
                # Пробуем восстановить
                subprocess.run(["git", "stash", "pop"], cwd=self._repo_path, capture_output=True, timeout=10)
                return False, f"Ошибка обновления: {result.stderr}"

            # Восстанавливаем локальные изменения
            subprocess.run(
                ["git", "stash", "pop"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            logger.info("Обновление успешно завершено")
            return True, "Обновление успешно! Перезапустите приложение."

        except subprocess.TimeoutExpired:
            logger.error("Таймаут при обновлении")
            return False, "Таймаут при обновлении"
        except FileNotFoundError:
            logger.error("Git не установлен")
            return False, "Git не установлен в системе"
        except Exception as e:
            logger.exception(f"Ошибка обновления: {e}")
            return False, f"Ошибка: {str(e)}"

    def get_current_version(self) -> str:
        """Получить текущую версию (хеш коммита)"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
        except Exception:
            return "unknown"

    def get_last_commit_info(self) -> str:
        """Получить информацию о последнем коммите"""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%h - %s (%ci)"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "Не удалось получить информацию"
        except Exception as e:
            return f"Ошибка: {str(e)}"
