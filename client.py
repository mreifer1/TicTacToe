import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QGridLayout,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QMenuBar,
    QMenu,
)
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction

class GameLogic:
    def __init__(self):
        self.board_size = 3
        self.current_player = 'X'
        self.game_board = [['' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.game_over = False

    def button_clicked(self, row, col):
        if not self.game_over and self.game_board[row][col] == '':
            self.game_board[row][col] = self.current_player
            if self.check_win(self.current_player):
                self.game_over = True
                return f"Player {self.current_player} wins!"
            elif self.check_draw():
                self.game_over = True
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
        return f"Current Player: {self.current_player}"

class TicTacToeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_logic = GameLogic()
        self._setup_ui()
        self._update_message(self.game_logic.current_player)

    def _setup_ui(self):
        self.setWindowTitle("Tic-Tac-Toe")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self._create_menu_bar()
        self._create_game_board()
        self._create_controls()
        self.main_layout.addWidget(self.board_widget)
        self.main_layout.addWidget(self.controls_bottom_widget)

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
        menu_bar.addMenu(game_menu)
        self.setMenuBar(menu_bar)

    def _create_game_board(self):
        self.board_widget = QWidget()
        self.grid_layout = QGridLayout(self.board_widget)
        self.grid_layout.setSpacing(2)
        self.board_widget.setStyleSheet("background-color: #000;")
        self.buttons = []
        for row in range(self.game_logic.board_size):
            row_buttons = []
            for col in range(self.game_logic.board_size):
                button = QPushButton("")
                button.setMinimumSize(QSize(80, 80))
                button.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: none;
                        font-size: 36px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                    }
                    QPushButton:disabled {
                        background-color: #e0e0e0;
                        color: black;
                    }
                """)
                button.clicked.connect(lambda _, r=row, c=col: self.button_clicked(r, c))
                self.grid_layout.addWidget(button, row, col)
                row_buttons.append(button)
            self.buttons.append(row_buttons)

    def _create_controls(self):
        self.controls_bottom_widget = QWidget()
        controls_bottom_layout = QHBoxLayout(self.controls_bottom_widget)
        self.message_label = QLabel("Welcome!")
        self.reset_button = QPushButton("Reset Game")
        self.reset_button.clicked.connect(self.reset_game)
        controls_bottom_layout.addWidget(self.message_label)
        controls_bottom_layout.addWidget(self.reset_button)
        controls_bottom_layout.addStretch(1)

    def button_clicked(self, row, col):
        result = self.game_logic.button_clicked(row, col)
        if result:
            self.buttons[row][col].setText(self.game_logic.game_board[row][col])
            self.buttons[row][col].setEnabled(False)
            if "wins" in result or "draw" in result:
                self._show_game_over_message(result, "wins" in result)
            else:
                self._update_message(result)

    def _show_game_over_message(self, message, win):
        if win:
            self.message_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.message_label.setStyleSheet("color: black; font-weight: bold;")
        self.message_label.setText(message)
        self._disable_all_buttons()

    def _disable_all_buttons(self):
        for row_buttons in self.buttons:
            for button in row_buttons:
                button.setEnabled(False)

    def reset_game(self):
        message = self.game_logic.reset_game()
        for row_buttons in self.buttons:
            for button in row_buttons:
                button.setText("")
                button.setEnabled(True)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: none;
                        font-size: 36px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                    }
                    QPushButton:disabled {
                        background-color: #e0e0e0;
                        color: black;
                    }
                """)
        self._update_message(message)
        self.message_label.setStyleSheet("")

    def _update_message(self, message):
        self.message_label.setText(f"Current Player: {message}")
        self.message_label.setStyleSheet("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TicTacToeWindow()
    window.show()
    sys.exit(app.exec())