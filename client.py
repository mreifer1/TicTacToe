import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton
from PySide6.QtCore import QSize

class TicTacToeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tic-Tac-Toe")
        self.setGeometry(100, 100, 300, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.grid_layout = QGridLayout(self.central_widget)
        self.grid_layout.setSpacing(0)  # Remove spacing between grid cells

        self.buttons = []
        for row in range(3):
            row_buttons = []
            for col in range(3):
                button = QPushButton("")
                button.setMinimumSize(QSize(100, 100))

                # board cell styling
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
                """)

                self.grid_layout.addWidget(button, row, col)
                row_buttons.append(button)
            self.buttons.append(row_buttons)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TicTacToeWindow()
    window.show()
    sys.exit(app.exec())