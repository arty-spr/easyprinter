"""
Стили для приложения EasyPrinter
"""


class Styles:
    """Стили и цвета приложения"""

    # Цвета
    BACKGROUND_COLOR = "#F5F5F5"
    CARD_BACKGROUND = "#FFFFFF"
    PRIMARY_COLOR = "#2196F3"
    SUCCESS_COLOR = "#4CAF50"
    WARNING_COLOR = "#FF9800"
    DANGER_COLOR = "#F44336"
    PURPLE_COLOR = "#9C27B0"

    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"

    # Размеры шрифтов
    FONT_SIZE_SMALL = 12
    FONT_SIZE_NORMAL = 14
    FONT_SIZE_LARGE = 18
    FONT_SIZE_TITLE = 28
    FONT_SIZE_ICON = 48

    @staticmethod
    def get_main_stylesheet() -> str:
        """Получить основной стиль приложения"""
        return f"""
            QMainWindow, QWidget {{
                background-color: {Styles.BACKGROUND_COLOR};
                font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
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
            }}

            QPushButton {{
                background-color: {Styles.PRIMARY_COLOR};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: #1976D2;
            }}

            QPushButton:pressed {{
                background-color: #1565C0;
            }}

            QPushButton:disabled {{
                background-color: #BDBDBD;
                color: #9E9E9E;
            }}

            QPushButton[class="success"] {{
                background-color: {Styles.SUCCESS_COLOR};
            }}

            QPushButton[class="success"]:hover {{
                background-color: #43A047;
            }}

            QPushButton[class="warning"] {{
                background-color: {Styles.WARNING_COLOR};
            }}

            QPushButton[class="warning"]:hover {{
                background-color: #FB8C00;
            }}

            QPushButton[class="danger"] {{
                background-color: {Styles.DANGER_COLOR};
            }}

            QPushButton[class="danger"]:hover {{
                background-color: #E53935;
            }}

            QPushButton[class="purple"] {{
                background-color: {Styles.PURPLE_COLOR};
            }}

            QPushButton[class="purple"]:hover {{
                background-color: #8E24AA;
            }}

            QPushButton[class="secondary"] {{
                background-color: #757575;
            }}

            QPushButton[class="secondary"]:hover {{
                background-color: #616161;
            }}

            QPushButton[class="nav-button"] {{
                min-width: 180px;
                min-height: 150px;
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: bold;
                border-radius: 12px;
            }}

            QLineEdit, QTextEdit {{
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                color: {Styles.TEXT_PRIMARY};
            }}

            QLineEdit:focus, QTextEdit:focus {{
                border-color: {Styles.PRIMARY_COLOR};
            }}

            QLineEdit:disabled {{
                background-color: #F5F5F5;
                color: {Styles.TEXT_SECONDARY};
            }}

            QComboBox {{
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                color: {Styles.TEXT_PRIMARY};
                min-height: 20px;
            }}

            QComboBox:focus {{
                border-color: {Styles.PRIMARY_COLOR};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid {Styles.TEXT_SECONDARY};
                margin-right: 10px;
            }}

            QComboBox QAbstractItemView {{
                background-color: white;
                border: 1px solid #E0E0E0;
                selection-background-color: {Styles.PRIMARY_COLOR};
                selection-color: white;
            }}

            QSlider::groove:horizontal {{
                border: none;
                height: 8px;
                background: #E0E0E0;
                border-radius: 4px;
            }}

            QSlider::handle:horizontal {{
                background: {Styles.PRIMARY_COLOR};
                border: none;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}

            QSlider::handle:horizontal:hover {{
                background: #1976D2;
            }}

            QSlider::sub-page:horizontal {{
                background: {Styles.PRIMARY_COLOR};
                border-radius: 4px;
            }}

            QCheckBox {{
                font-size: {Styles.FONT_SIZE_NORMAL}px;
                color: {Styles.TEXT_PRIMARY};
                spacing: 10px;
            }}

            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
                border: 2px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
            }}

            QCheckBox::indicator:checked {{
                background-color: {Styles.PRIMARY_COLOR};
                border-color: {Styles.PRIMARY_COLOR};
            }}

            QProgressBar {{
                border: none;
                border-radius: 5px;
                background-color: #E0E0E0;
                text-align: center;
                font-size: {Styles.FONT_SIZE_SMALL}px;
            }}

            QProgressBar::chunk {{
                background-color: {Styles.SUCCESS_COLOR};
                border-radius: 5px;
            }}

            QScrollArea {{
                border: none;
                background-color: transparent;
            }}

            QScrollBar:vertical {{
                background-color: #F5F5F5;
                width: 12px;
                border-radius: 6px;
            }}

            QScrollBar::handle:vertical {{
                background-color: #BDBDBD;
                border-radius: 6px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: #9E9E9E;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QGroupBox {{
                background-color: {Styles.CARD_BACKGROUND};
                border: none;
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-size: {Styles.FONT_SIZE_LARGE}px;
                font-weight: 600;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                color: {Styles.TEXT_PRIMARY};
            }}

            QFrame[class="card"] {{
                background-color: {Styles.CARD_BACKGROUND};
                border: none;
                border-radius: 12px;
            }}

            QFrame[class="statusbar"] {{
                background-color: {Styles.CARD_BACKGROUND};
                border-top: 1px solid #E0E0E0;
            }}
        """

    @staticmethod
    def get_card_style() -> str:
        """Стиль для карточек"""
        return f"""
            background-color: {Styles.CARD_BACKGROUND};
            border-radius: 12px;
            padding: 20px;
        """

    @staticmethod
    def get_nav_button_style(color: str) -> str:
        """Стиль для навигационных кнопок"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 12px;
                min-width: 180px;
                min-height: 150px;
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
    def _darken_color(hex_color: str, factor: float = 0.1) -> str:
        """Затемнить цвет"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))

        return f"#{r:02x}{g:02x}{b:02x}"
