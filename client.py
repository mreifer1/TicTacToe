import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import QSize
from PySide6.QtGui import QPalette, QColor

class TicTacToeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tic-Tac-Toe")
        self.setGeometry(100, 100, 450, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)

        # Left Panel for Controls
        self.controls_panel = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_panel)
        self.controls_panel.setStyleSheet("background-color: #f0f0f0; border-right: 1px solid #ccc;")

        self.reset_button = QPushButton("Reset Game")
        self.reset_button.clicked.connect(self.reset_game)
        self.controls_layout.addWidget(self.reset_button)

        self.message_label = QLabel("Welcome!")
        self.controls_layout.addWidget(self.message_label)

        self.controls_layout.addStretch(1)

        self.main_layout.addWidget(self.controls_panel)

        # Board
        self.board_widget = QWidget()
        self.grid_layout = QGridLayout(self.board_widget)
        self.grid_layout.setSpacing(0)

        self.buttons = []
        for row in range(3):
            row_buttons = []
            for col in range(3):
                button = QPushButton("")
                button.setMinimumSize(QSize(100, 100))
                button.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: 1px solid black;
                        font-size: 40px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: lightgray;
                    }
                    QPushButton:disabled {
                        background-color: #e0e0e0; /* Slightly darker when disabled */
                        color: black; /* Ensure text is still visible when disabled */
                    }
                """)
                button.clicked.connect(lambda _, r=row, c=col: self.button_clicked(r, c))
                self.grid_layout.addWidget(button, row, col)
                row_buttons.append(button)
            self.buttons.append(row_buttons)

        self.main_layout.addWidget(self.board_widget)

        self.current_player = 'X'
        self.game_board = [['' for _ in range(3)] for _ in range(3)]
        self.game_over = False
        self.update_message()

    def button_clicked(self, row, col):
        if not self.game_over and self.game_board[row][col] == '':
            self.buttons[row][col].setText(self.current_player)
            self.game_board[row][col] = self.current_player
            self.buttons[row][col].setEnabled(False)

            if self.check_win(self.current_player):
                self.game_over = True
                self.show_game_over_message(f"Player {self.current_player} wins!", win=True)
            elif self.check_draw():
                self.game_over = True
                self.show_game_over_message("DRAW!")
            else:
                self.switch_player()
                self.update_message()

    def switch_player(self):
        if self.current_player == 'X':
            self.current_player = 'O'
        else:
            self.current_player = 'X'

    def check_win(self, player):
        for row in self.game_board:
            if all(cell == player for cell in row):
                return True
        for col in range(3):
            if all(self.game_board[row][col] == player for row in range(3)):
                return True
        if all(self.game_board[i][i] == player for i in range(3)):
            return True
        if all(self.game_board[i][2 - i] == player for i in range(3)):
            return True
        return False

    def check_draw(self):
        return all(cell != '' for row in self.game_board for cell in row)

    def show_game_over_message(self, message, win=False):
        if win:
            self.message_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.message_label.setStyleSheet("color: black; font-weight: bold;") # Or reset to default
        self.message_label.setText(message)
        self.disable_all_buttons()

    def disable_all_buttons(self):
        for row_buttons in self.buttons:
            for button in row_buttons:
                button.setEnabled(False)

    def reset_game(self):
        self.current_player = 'X'
        self.game_board = [['' for _ in range(3)] for _ in range(3)]
        self.game_over = False
        for row_buttons in self.buttons:
            for button in row_buttons:
                button.setText("")
                button.setEnabled(True)
                # Reset button style (important)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: 1px solid black;
                        font-size: 40px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: lightgray;
                    }
                    QPushButton:disabled {
                        background-color: #e0e0e0;
                        color: black;
                    }
                """)
        self.update_message()
        self.message_label.setStyleSheet("") # Clear any specific styling

    def update_message(self, message=None):
        if message:
            self.message_label.setText(message)
        else:
            self.message_label.setText(f"Current Player: {self.current_player}")
            self.message_label.setStyleSheet("") # Reset style for turn messages

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TicTacToeWindow()
    window.show()
    sys.exit(app.exec())