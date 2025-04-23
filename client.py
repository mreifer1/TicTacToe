import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMenuBar,
    QMenu,
    QStyleFactory,
    
)
from PySide6.QtCore import QSize, Qt, QPointF
from PySide6.QtGui import QAction, QPainter, QPen, QFont, QPalette, QColor, QResizeEvent

class GameLogic:
    def __init__(self):
        self.board_size = 3
        self.current_player = 'X'
        self.game_board = [['' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.game_over = False
        self.winner = None  # Track the winner explicitly

    def button_clicked(self, row, col):
        """Handles a move (row,col). Returns a status message if move changes state."""
        if not self.game_over and self.game_board[row][col] == '':
            self.game_board[row][col] = self.current_player
            if self.check_win(self.current_player):
                self.game_over = True
                self.winner = self.current_player
                return f"Player {self.current_player} wins!"
            elif self.check_draw():
                self.game_over = True
                self.winner = None
                return "It's a draw!"
            else:
                self._switch_player()
                return f"Current Player: {self.current_player}"
        return None

    def _switch_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def check_win(self, player):
        board = self.game_board
        size = self.board_size
        # Check rows
        for row in board:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(size):
            if all(board[row][col] == player for row in range(size)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(size)):
            return True
        if all(board[i][size - 1 - i] == player for i in range(size)):
            return True
        return False

    def check_draw(self):
        return all(cell != '' for row in self.game_board for cell in row)

    def reset_game(self):
        self.current_player = 'X'

        self.game_board = [['' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.game_over = False
        self.winner = None
        return f"Current Player: {self.current_player}"

class BoardWidget(QWidget):
    """
    A custom widget that draws the Tic-Tac-Toe board, the X's and O's,
    and a large X or O overlay if there's a winner.
    """
    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game_logic = game_logic
        self.setMinimumSize(QSize(300, 300))  # A decent default

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Fill background (dark gray)
        painter.fillRect(self.rect(), QColor("#333"))

        # Calculate cell size
        w = self.width()
        h = self.height()
        size = self.game_logic.board_size
        cell_w = w / size
        cell_h = h / size

        # Draw grid lines (slightly lighter dark gray)
        pen = QPen(QColor("#555"), 2)
        painter.setPen(pen)

        # Draw the 2 internal lines vertically and horizontally
        for i in range(1, size):
            painter.drawLine(i * cell_w, 0, i * cell_w, h)
            painter.drawLine(0, i * cell_h, w, i * cell_h)

        # Draw X or O in each cell
        for row in range(size):
            for col in range(size):
                symbol = self.game_logic.game_board[row][col]
                if symbol:
                    center_x = col * cell_w + cell_w / 2
                    center_y = row * cell_h + cell_h / 2
                    radius = min(cell_w, cell_h) / 2 - 10

                    if symbol == 'X':
                        # Draw X in a light blue color
                        pen = QPen(QColor("#8acaff"), 4)
                        painter.setPen(pen)
                        painter.drawLine(center_x - radius, center_y - radius,
                                         center_x + radius, center_y + radius)
                        painter.drawLine(center_x + radius, center_y - radius,
                                         center_x - radius, center_y + radius)
                    else:
                        # Draw O in a light red color
                        pen = QPen(QColor("#ff8a8a"), 4)
                        painter.setPen(pen)
                        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # If the game is over and there's a winner, draw a large overlay symbol
        if self.game_logic.game_over and self.game_logic.winner is not None:
            winner = self.game_logic.winner
            # Use a thicker pen for the large overlay
            pen = QPen(Qt.white, 8)
            painter.setPen(pen)
            font = QFont("Arial", int(min(w, h) * 0.6), QFont.Bold)
            painter.setFont(font)
            painter.setPen(QPen(QColor("#eee"), 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawText(self.rect(), Qt.AlignCenter, winner)

    def mouseReleaseEvent(self, event):
        # If the game is already over, ignore clicks
        if self.game_logic.game_over:
            return

        # Determine which cell was clicked
        w = self.width()
        h = self.height()
        size = self.game_logic.board_size
        cell_w = w / size
        cell_h = h / size

        col = int(event.x() // cell_w)
        row = int(event.y() // cell_h)

        if 0 <= row < size and 0 <= col < size:
            result = self.game_logic.button_clicked(row, col)
            if result:
                # Force redraw
                self.update()
                # Update the parent window’s message label if applicable
                if hasattr(self.parent(), "_update_message"):
                    self.parent()._update_message(result)
                # Show "win/draw" message
                if "wins" in result or "draw" in result:
                    if hasattr(self.parent(), "_show_game_over_message"):
                        self.parent()._show_game_over_message(result, "wins" in result)

class TicTacToeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_logic = GameLogic()
        self.board_widget = BoardWidget(self.game_logic, parent=self) # Initialize here
        self._setup_ui()
        self._update_message(f"Current Player: {self.game_logic.current_player}")
        self.setMinimumSize(self.sizeHint()) # Set minimum size based on content

    def _setup_ui(self):
        self.setWindowTitle("Tic-Tac-Toe")

        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #222; }
            QMenuBar { background-color: #333; color: #eee; }
            QMenuBar::item { color: #eee; }
            QMenuBar::item:selected { background-color: #555; }
            QMenu { background-color: #333; color: #eee; border: 1px solid #555; }
            QMenu::item { color: #eee; padding: 8px 20px; }
            QMenu::item:selected { background-color: #555; }
            QPushButton { background-color: #444; color: #eee; border: 1px solid #555; padding: 8px 15px; border-radius: 5px; }
            QPushButton:hover { background-color: #555; }
            QLabel { color: #eee; }
        """)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self._create_menu_bar()

        # Create the custom board widget (already initialized)
        self.main_layout.addWidget(self.board_widget)

        # Bottom controls (message label + reset button)
        self._create_controls()
        self.main_layout.addWidget(self.controls_bottom_widget)

        # Calculate initial window size
        board_size = self.board_widget.sizeHint()
        controls_size = self.controls_bottom_widget.sizeHint()
        menu_bar_height = self.menuBar().height() if self.menuBar() else 0
        vertical_spacing = self.main_layout.spacing() * 2 # Account for spacing between widgets
        initial_width = max(board_size.width(), controls_size.width()) + self.frameGeometry().width() - self.geometry().width() + 20 # Added some padding
        initial_height = board_size.height() + controls_size.height() + menu_bar_height + vertical_spacing + self.frameGeometry().height() - self.geometry().height() + 40 # Added some padding
        self.setGeometry(100, 100, initial_width, initial_height)

    def _create_menu_bar(self):
        menu_bar = QMenuBar()
        game_menu = QMenu("Game", self)
        reset_action = QAction("New Game", self)
        reset_action.triggered.connect(self.reset_game)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)

        game_menu.addAction(reset_action)
        game_menu.addSeparator()
        game_menu.addAction(quit_action)
        menu_bar.addMenu(game_menu) # Corrected line
        self.setMenuBar(menu_bar)

    def _create_controls(self):
        self.controls_bottom_widget = QWidget()
        controls_bottom_layout = QHBoxLayout(self.controls_bottom_widget)
        self.controls_bottom_widget.setStyleSheet("background-color: transparent;") # Make background transparent

        self.message_label = QLabel("")
        font = QFont()
        font.setPointSize(12)
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Align text to the left

        self.reset_button = QPushButton("Reset Game")
        self.reset_button.clicked.connect(self.reset_game)

        controls_bottom_layout.addWidget(self.message_label)
        controls_bottom_layout.addStretch(1) # Push button to the right
        controls_bottom_layout.addWidget(self.reset_button)
        self.controls_bottom_widget.setLayout(controls_bottom_layout) # Ensure layout is set

    def _update_message(self, message):
        self.message_label.setText(message)

    def _show_game_over_message(self, message, win):
        # If there's a winner, highlight in a color
        if win:
            self.message_label.setStyleSheet("color: lime; font-weight: bold;")
        else:
            self.message_label.setStyleSheet("color: yellow; font-weight: bold;")
        self.message_label.setText(message)

    def reset_game(self):
        msg = self.game_logic.reset_game()
        self._update_message(f"Current Player: {self.game_logic.current_player}")
        # Clear any "winner" color
        self.message_label.setStyleSheet("")
        # Update/redraw the board
        self.board_widget.update()

    def resizeEvent(self, event: QResizeEvent):
        """Maintain a square aspect ratio for the board."""
        current_width = self.central_widget.width()
        board_height = current_width  # Make height equal to width for a square board

        # Calculate the total desired height for the window
        menu_bar_height = self.menuBar().height() if self.menuBar() else 0
        controls_height = self.controls_bottom_widget.sizeHint().height()
        vertical_spacing = self.main_layout.spacing() * 2

        desired_height = menu_bar_height + board_height + controls_height + vertical_spacing + self.frameGeometry().height() - self.geometry().height() + 20 # Added some extra for frame

        if self.height() != desired_height:
            self.resize(current_width + (self.frameGeometry().width() - self.geometry().width()), desired_height)
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply a dark style that is often close to macOS native dark mode
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = TicTacToeWindow()
    window.show()
    sys.exit(app.exec())