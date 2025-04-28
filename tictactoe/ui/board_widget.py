from PySide6.QtWidgets import (
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    QPointF,
    QRect
)
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QFont
)

class BoardWidget(QWidget):
    cell_clicked = Signal(int, int)
    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game_logic = game_logic
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setMinimumSize(QSize(150, 150))
        self._accept_clicks = True

    def set_accept_clicks(self, accept): self._accept_clicks = accept
    def heightForWidth(self, width): return width
    def hasHeightForWidth(self): return True

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            w = self.width(); h = self.height(); side = min(w, h)
            offset_x = (w - side) / 2; offset_y = (h - side) / 2
            painter.fillRect(self.rect(), QColor("#333"))
            size = self.game_logic.board_size; cell_size = side / size
            pen = QPen(QColor("#555"), 2); painter.setPen(pen)
            for i in range(1, size):
                x = offset_x + i * cell_size; painter.drawLine(int(x), int(offset_y), int(x), int(offset_y + side))
                y = offset_y + i * cell_size; painter.drawLine(int(offset_x), int(y), int(offset_x + side), int(y))
            for row in range(size):
                for col in range(size):
                    symbol = self.game_logic.game_board[row][col]
                    if symbol:
                        center_x = offset_x + col * cell_size + cell_size / 2
                        center_y = offset_y + row * cell_size + cell_size / 2
                        radius = cell_size / 2 * 0.7
                        if symbol == 'X':
                            pen = QPen(QColor("#8acaff"), 4); painter.setPen(pen)
                            painter.drawLine(QPointF(center_x - radius, center_y - radius), QPointF(center_x + radius, center_y + radius))
                            painter.drawLine(QPointF(center_x + radius, center_y - radius), QPointF(center_x - radius, center_y + radius))
                        else:
                            pen = QPen(QColor("#ff8a8a"), 4); painter.setPen(pen)
                            painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
            if self.game_logic.game_over and self.game_logic.winner:
                winner = self.game_logic.winner
                font = QFont("Arial", int(side * 0.6), QFont.Bold); painter.setFont(font)
                color = QColor("#8acaff") if winner == 'X' else QColor("#ff8a8a")
                pen = QPen(color, 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin); painter.setPen(pen)
                draw_rect = QRect(int(offset_x), int(offset_y), int(side), int(side))
                painter.drawText(draw_rect, Qt.AlignCenter, winner)
        finally: pass

    def mouseReleaseEvent(self, event):
        if not self._accept_clicks or self.game_logic.game_over: return
        w = self.width(); h = self.height(); side = min(w, h)
        offset_x = (w - side) / 2; offset_y = (h - side) / 2
        if not (offset_x <= event.position().x() < offset_x + side and offset_y <= event.position().y() < offset_y + side): return
        cell_size = side / self.game_logic.board_size;
        if cell_size <= 0: return
        click_x = event.position().x() - offset_x; click_y = event.position().y() - offset_y
        col = int(click_x // cell_size); row = int(click_y // cell_size)
        row = max(0, min(row, self.game_logic.board_size - 1))
        col = max(0, min(col, self.game_logic.board_size - 1))
        self.cell_clicked.emit(row, col)
