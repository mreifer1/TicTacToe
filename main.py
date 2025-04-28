import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from tictactoe.ui.main_window import TicTacToeWindow

# -----------------------------------------------------------------------------
# COLOR CONSTANTS
# -----------------------------------------------------------------------------

WINDOW_COLOR = QColor(53, 53, 53)
WINDOW_TEXT_COLOR = Qt.white
BASE_COLOR = QColor(35, 35, 35)
ALT_BASE_COLOR = QColor(53, 53, 53)
TOOLTIP_BASE_COLOR = Qt.white
TOOLTIP_TEXT_COLOR = Qt.black
TEXT_COLOR = Qt.white
BUTTON_COLOR = QColor(66, 66, 66)
BUTTON_TEXT_COLOR = Qt.white
BRIGHT_TEXT_COLOR = Qt.red
LINK_COLOR = QColor(42, 130, 218)
HIGHLIGHT_COLOR = QColor(42, 130, 218)
HIGHLIGHTED_TEXT_COLOR = Qt.white
PLACEHOLDER_TEXT_COLOR = QColor(160, 160, 160)

DISABLED_TEXT_COLOR = QColor(127, 127, 127)
DISABLED_BUTTON_TEXT_COLOR = QColor(127, 127, 127)
DISABLED_WINDOW_TEXT_COLOR = QColor(127, 127, 127)

# -----------------------------------------------------------------------------
# PALETTE SETUP
# -----------------------------------------------------------------------------

def apply_default_palette(app: QApplication):
    """
    Apply the default dark theme palette using predefined constants.
    """
    palette = QPalette()
    # Standard roles
    palette.setColor(QPalette.Window, WINDOW_COLOR)
    palette.setColor(QPalette.WindowText, WINDOW_TEXT_COLOR)
    palette.setColor(QPalette.Base, BASE_COLOR)
    palette.setColor(QPalette.AlternateBase, ALT_BASE_COLOR)
    palette.setColor(QPalette.ToolTipBase, TOOLTIP_BASE_COLOR)
    palette.setColor(QPalette.ToolTipText, TOOLTIP_TEXT_COLOR)
    palette.setColor(QPalette.Text, TEXT_COLOR)
    palette.setColor(QPalette.Button, BUTTON_COLOR)
    palette.setColor(QPalette.ButtonText, BUTTON_TEXT_COLOR)
    palette.setColor(QPalette.BrightText, BRIGHT_TEXT_COLOR)
    palette.setColor(QPalette.Link, LINK_COLOR)
    palette.setColor(QPalette.Highlight, HIGHLIGHT_COLOR)
    palette.setColor(QPalette.HighlightedText, HIGHLIGHTED_TEXT_COLOR)
    # Placeholder text (e.g., QLineEdit placeholder)
    palette.setColor(QPalette.PlaceholderText, PLACEHOLDER_TEXT_COLOR)
    # Disabled roles
    palette.setColor(QPalette.Disabled, QPalette.Text, DISABLED_TEXT_COLOR)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, DISABLED_BUTTON_TEXT_COLOR)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, DISABLED_WINDOW_TEXT_COLOR)
    app.setPalette(palette)

# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Apply default dark theme
    apply_default_palette(app)

    window = TicTacToeWindow()
    window.show()
    sys.exit(app.exec())