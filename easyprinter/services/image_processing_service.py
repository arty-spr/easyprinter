"""
Сервис обработки изображений (яркость, контраст, резкость, гамма)
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Union

from ..models import ImageAdjustments


class ImageProcessingService:
    """Сервис обработки изображений"""

    def apply_adjustments(self, source: Image.Image, adjustments: ImageAdjustments) -> Image.Image:
        """Применить все настройки к изображению"""
        result = source.copy()

        if adjustments.brightness != 0 or adjustments.contrast != 0:
            result = self.apply_brightness_contrast(result, adjustments.brightness, adjustments.contrast)

        if abs(adjustments.gamma - 1.0) > 0.01:
            result = self.apply_gamma(result, adjustments.gamma)

        if adjustments.sharpness > 0:
            result = self.apply_sharpness(result, adjustments.sharpness)

        return result

    def apply_brightness_contrast(self, source: Image.Image, brightness: int, contrast: int) -> Image.Image:
        """Применить яркость и контрастность"""
        result = source

        # Яркость: преобразуем -100..+100 в фактор 0..2
        if brightness != 0:
            brightness_factor = 1.0 + (brightness / 100.0)
            enhancer = ImageEnhance.Brightness(result)
            result = enhancer.enhance(brightness_factor)

        # Контраст: преобразуем -100..+100 в фактор 0..2
        if contrast != 0:
            contrast_factor = 1.0 + (contrast / 100.0)
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(contrast_factor)

        return result

    def apply_gamma(self, source: Image.Image, gamma: float) -> Image.Image:
        """Применить гамма-коррекцию"""
        # Создаём таблицу гамма-коррекции
        inv_gamma = 1.0 / gamma
        gamma_table = [int((i / 255.0) ** inv_gamma * 255) for i in range(256)]

        # Применяем к каждому каналу
        if source.mode == 'RGBA':
            r, g, b, a = source.split()
            r = r.point(gamma_table)
            g = g.point(gamma_table)
            b = b.point(gamma_table)
            return Image.merge('RGBA', (r, g, b, a))
        elif source.mode == 'RGB':
            r, g, b = source.split()
            r = r.point(gamma_table)
            g = g.point(gamma_table)
            b = b.point(gamma_table)
            return Image.merge('RGB', (r, g, b))
        else:
            return source.point(gamma_table)

    def apply_sharpness(self, source: Image.Image, amount: int) -> Image.Image:
        """Применить резкость (Unsharp Mask)"""
        if amount <= 0:
            return source.copy()

        # Нормализуем amount (0-100) к фактору резкости (1-3)
        sharpness_factor = 1.0 + (amount / 50.0)

        enhancer = ImageEnhance.Sharpness(source)
        return enhancer.enhance(sharpness_factor)

    def apply_convolution(self, source: Image.Image, kernel: list) -> Image.Image:
        """Применить свёрточный фильтр"""
        # Преобразуем ядро в формат PIL
        size = int(len(kernel) ** 0.5)
        kernel_filter = ImageFilter.Kernel(
            size=(size, size),
            kernel=kernel,
            scale=sum(kernel) if sum(kernel) != 0 else 1,
            offset=0
        )
        return source.filter(kernel_filter)

    def resize_image(self, source: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """Изменить размер изображения с сохранением пропорций"""
        width, height = source.size
        ratio = min(max_width / width, max_height / height)

        if ratio < 1:
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            return source.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return source.copy()

    def convert_to_grayscale(self, source: Image.Image) -> Image.Image:
        """Конвертировать в градации серого"""
        return source.convert('L')

    def rotate_image(self, source: Image.Image, angle: int) -> Image.Image:
        """Повернуть изображение на заданный угол"""
        return source.rotate(angle, expand=True)
