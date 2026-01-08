"""
Настройки обработки изображения (яркость, контраст, резкость, гамма)
"""

from dataclasses import dataclass, field
import copy


@dataclass
class ImageAdjustments:
    """Настройки обработки изображения"""

    # Яркость (-100 до +100)
    brightness: int = 0

    # Контрастность (-100 до +100)
    contrast: int = 0

    # Резкость (0 до 100)
    sharpness: int = 0

    # Гамма (0.1 до 3.0)
    gamma: float = 1.0

    @property
    def has_changes(self) -> bool:
        """Проверяет, есть ли изменения относительно значений по умолчанию"""
        return (
            self.brightness != 0 or
            self.contrast != 0 or
            self.sharpness != 0 or
            abs(self.gamma - 1.0) > 0.01
        )

    def reset(self) -> None:
        """Сбросить все настройки к значениям по умолчанию"""
        self.brightness = 0
        self.contrast = 0
        self.sharpness = 0
        self.gamma = 1.0

    def clone(self) -> 'ImageAdjustments':
        """Создает копию настроек"""
        return copy.deepcopy(self)
