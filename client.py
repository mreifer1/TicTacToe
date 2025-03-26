import sys
from PySide6.QtWidgets import QApplication, QMainWindow

class TicTacToeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tic-Tac-Toe")
        self.setGeometry(100, 100, 300, 300)  # x, y, width, height

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TicTacToeWindow()
    window.show()
    sys.exit(app.exec())