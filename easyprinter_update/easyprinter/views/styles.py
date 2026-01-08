"""
Стили для приложения EasyPrinter
Оптимизировано для пожилых пользователей
"""

import platform


class Styles:
    """Стили и цвета приложения"""

    # Цвета (улучшенный контраст)
    BACKGROUND_COLOR = "#F5F5F5"
    CARD_BACKGROUND = "#FFFFFF"
    PRIMARY_COLOR = "#1976D2"  # Более насыщенный синий
    SUCCESS_COLOR = "#2E7D32"  # Более насыщенный зелёный
    WARNING_COLOR = "#F57C00"  # Более насыщенный оранжевый
    DANGER_COLOR = "#D32F2F"   # Более насыщенный красный
    PURPLE_COLOR = "#7B1FA2"   # Более насыщенный фиолетовый

    TEXT_PRIMARY = "#1A1A1A"   # Почти чёрный для максимального контраста
    TEXT_SECONDARY = "#424242" # Тёмно-серый вместо светло-серого

    # Увеличенные размеры шрифтов для пожилых
    FONT_SIZE_SMALL = 16
    FONT_SIZE_NORMAL = 18
    FONT_SIZE_LARGE = 24
    FONT_SIZE_TITLE = 36
    FONT_SIZE_ICON = 64

    # Минимальные размеры кликабельных элементов
    MIN_BUTTON_HEIGHT = 60
    MIN_TOUCH_TARGET = 48

    @staticmethod
    def get_main_stylesheet() -> str:
        """Получить основной стиль приложения"""
        return f"""
            QMainWindow, QWidget {{
                background-color: {Styles.BACKGROUND_COLOR};
                font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
            }}

            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                font-size: {Styles.FONT_SIZE_NORMAL}px;
            }}

            QLabel[class="title"] {{
                font-size: {Styles.FONT_SIZE_TITLE}px;
                font-weight: bold;
                color: {Styles.TEXT_PRIMARY};
            }}

            QLabel[class="subtitle"] {{
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: 600;
                color: {Styles.TEXT_PRIMARY};
            }}

            QLabel[class="secondary"] {{
                color: {Styles.TEXT_SECONDARY};
                font-size: {Styles.FONT_SIZE_NORMAL}px;
            }}

            QPushButton {{
                background-color: {Styles.PRIMARY_COLOR};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: 600;
                min-height: {Styles.MIN_BUTTON_HEIGHT}px;
            }}

            QPushButton:hover {{
                background-color: #1565C0;
            }}

            QPushButton:pressed {{
                background-color: #0D47A1;
            }}

            QPushButton:disabled {{
                background-color: #9E9E9E;
                color: #E0E0E0;
            }}

            QLineEdit, QTextEdit {{
                background-color: white;
                border: 3px solid #BDBDBD;
                border-radius: 10px;
                padding: 12px 18px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                color: {Styles.TEXT_PRIMARY};
                min-height: 30px;
            }}

            QLineEdit:focus, QTextEdit:focus {{
                border-color: {Styles.PRIMARY_COLOR};
                border-width: 3px;
            }}

            QLineEdit:disabled {{
                background-color: #EEEEEE;
                color: {Styles.TEXT_SECONDARY};
            }}

            QComboBox {{
                background-color: white;
                border: 3px solid #BDBDBD;
                border-radius: 10px;
                padding: 12px 18px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                color: {Styles.TEXT_PRIMARY};
                min-height: 40px;
            }}

            QComboBox:focus {{
                border-color: {Styles.PRIMARY_COLOR};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 40px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 12px solid {Styles.TEXT_SECONDARY};
                margin-right: 15px;
            }}

            QComboBox QAbstractItemView {{
                background-color: white;
                border: 2px solid #BDBDBD;
                selection-background-color: {Styles.PRIMARY_COLOR};
                selection-color: white;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                padding: 5px;
            }}

            QComboBox QAbstractItemView::item {{
                min-height: 40px;
                padding: 10px;
            }}

            QSlider::groove:horizontal {{
                border: none;
                height: 12px;
                background: #BDBDBD;
                border-radius: 6px;
            }}

            QSlider::handle:horizontal {{
                background: {Styles.PRIMARY_COLOR};
                border: none;
                width: 28px;
                height: 28px;
                margin: -8px 0;
                border-radius: 14px;
            }}

            QSlider::handle:horizontal:hover {{
                background: #1565C0;
            }}

            QSlider::sub-page:horizontal {{
                background: {Styles.PRIMARY_COLOR};
                border-radius: 6px;
            }}

            QCheckBox {{
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                color: {Styles.TEXT_PRIMARY};
                spacing: 15px;
            }}

            QCheckBox::indicator {{
                width: 28px;
                height: 28px;
                border: 3px solid #BDBDBD;
                border-radius: 6px;
                background-color: white;
            }}

            QCheckBox::indicator:checked {{
                background-color: {Styles.PRIMARY_COLOR};
                border-color: {Styles.PRIMARY_COLOR};
            }}

            QProgressBar {{
                border: none;
                border-radius: 8px;
                background-color: #E0E0E0;
                text-align: center;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                min-height: 30px;
            }}

            QProgressBar::chunk {{
                background-color: {Styles.SUCCESS_COLOR};
                border-radius: 8px;
            }}

            QScrollArea {{
                border: none;
                background-color: transparent;
            }}

            QScrollBar:vertical {{
                background-color: #F5F5F5;
                width: 18px;
                border-radius: 9px;
            }}

            QScrollBar::handle:vertical {{
                background-color: #BDBDBD;
                border-radius: 9px;
                min-height: 50px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: #9E9E9E;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QGroupBox {{
                background-color: {Styles.CARD_BACKGROUND};
                border: 2px solid #E0E0E0;
                border-radius: 15px;
                padding: 25px;
                margin-top: 15px;
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: 600;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 8px 15px;
                color: {Styles.TEXT_PRIMARY};
                font-size: {Styles.FONT_SIZE_LARGE}px;
            }}

            QSpinBox {{
                background-color: white;
                border: 3px solid #BDBDBD;
                border-radius: 10px;
                padding: 10px 15px;
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: bold;
                min-height: 40px;
                min-width: 100px;
            }}

            QSpinBox:focus {{
                border-color: {Styles.PRIMARY_COLOR};
            }}

            QSpinBox::up-button, QSpinBox::down-button {{
                width: 35px;
                border: none;
            }}

            QSpinBox::up-arrow {{
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-bottom: 10px solid {Styles.TEXT_SECONDARY};
            }}

            QSpinBox::down-arrow {{
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 10px solid {Styles.TEXT_SECONDARY};
            }}

            QMessageBox {{
                background-color: {Styles.CARD_BACKGROUND};
            }}

            QMessageBox QLabel {{
                font-size: {Styles.FONT_SIZE_LARGE}px;
                color: {Styles.TEXT_PRIMARY};
                min-width: 400px;
            }}

            QMessageBox QPushButton {{
                min-width: 150px;
                min-height: 50px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
            }}

            QDialog {{
                background-color: {Styles.BACKGROUND_COLOR};
            }}

            QTabWidget::pane {{
                border: none;
                background-color: white;
                border-radius: 12px;
            }}

            QTabBar::tab {{
                background-color: #E0E0E0;
                padding: 18px 35px;
                margin-right: 6px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: 500;
            }}

            QTabBar::tab:selected {{
                background-color: white;
                font-weight: bold;
            }}

            QTabBar::tab:hover {{
                background-color: #F5F5F5;
            }}
        """

    @staticmethod
    def get_card_style() -> str:
        """Стиль для карточек"""
        return f"""
            background-color: {Styles.CARD_BACKGROUND};
            border-radius: 15px;
            padding: 25px;
        """

    @staticmethod
    def get_nav_button_style(color: str) -> str:
        """Стиль для навигационных кнопок"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 20px;
                min-width: 220px;
                min-height: 180px;
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Styles._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {Styles._darken_color(color, 0.2)};
            }}
        """

    @staticmethod
    def get_big_action_button_style(color: str) -> str:
        """Стиль для больших кнопок действий"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: 28px;
                font-weight: bold;
                border-radius: 15px;
                min-height: 100px;
            }}
            QPushButton:hover {{
                background-color: {Styles._darken_color(color)};
            }}
            QPushButton:disabled {{
                background-color: #9E9E9E;
            }}
        """

    @staticmethod
    def get_drop_zone_style(active: bool = False) -> str:
        """Стиль для зоны перетаскивания файлов"""
        if active:
            return f"""
                background-color: #E3F2FD;
                border: 4px dashed {Styles.PRIMARY_COLOR};
                border-radius: 20px;
            """
        return f"""
            background-color: #FAFAFA;
            border: 4px dashed #BDBDBD;
            border-radius: 20px;
        """

    @staticmethod
    def _darken_color(hex_color: str, factor: float = 0.15) -> str:
        """Затемнить цвет"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))

        return f"#{r:02x}{g:02x}{b:02x}"
