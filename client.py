import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QMenuBar, QMenu
from PySide6.QtCore import QSize
from PySide6.QtGui import QPalette, QColor, QAction

class TicTacToeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tic-Tac-Toe")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

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

        content_layout = QHBoxLayout()

        self.controls_panel = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_panel)

        self.reset_button = QPushButton("Reset Game")
        self.reset_button.clicked.connect(self.reset_game)

        self.message_label = QLabel("Welcome!")
        self.controls_layout.addWidget(self.message_label)
        self.controls_layout.addWidget(self.reset_button)

        self.controls_layout.addStretch(1)

        # Tic-Tac-Toe Board
        self.board_widget = QWidget()
        self.grid_layout = QGridLayout(self.board_widget)
        self.grid_layout.setSpacing(2) # Add spacing for grid lines

        self.board_widget.setStyleSheet("background-color: #000;") # Black background for grid lines

        self.buttons = []
        for row in range(3):
            row_buttons = []
            for col in range(3):
                button = QPushButton("")
                button.setMinimumSize(QSize(80, 80)) # Adjust button size
                button.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: none; /* Remove button borders */
                        font-size: 36px; /* Adjust font size */
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0; /* Lighter gray on hover */
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

        content_layout.addWidget(self.board_widget)

        
        controls_bottom_widget = QWidget()
        controls_bottom_layout = QHBoxLayout(controls_bottom_widget)
        controls_bottom_layout.addWidget(self.message_label)
        controls_bottom_layout.addWidget(self.reset_button)
        controls_bottom_layout.addStretch(1)

        self.main_layout.addLayout(content_layout)
        self.main_layout.addWidget(controls_bottom_widget)

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
                self.show_game_over_message("It's a draw!")
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
            self.message_label.setStyleSheet("color: black; font-weight: bold;")
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
        self.update_message()
        self.message_label.setStyleSheet("")

    def update_message(self, message=None):
        if message:
            self.message_label.setText(message)
        else:
            self.message_label.setText(f"Current Player: {self.current_player}")
            self.message_label.setStyleSheet("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TicTacToeWindow()
    window.show()
    sys.exit(app.exec())