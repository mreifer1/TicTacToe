from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal, QPointF, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont

class BoardWidget(QWidget):
    """
    custom widget to draw and click on tic-tac-toe board
    """
    cell_clicked = Signal(int, int)  # emits row, col on click

    def __init__(self, game_logic, parent=None):
        super().__init__(parent)
        self.game_logic = game_logic  # reference to game state
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setMinimumSize(QSize(150, 150))
        self._accept_clicks = True      # toggle click handling

    def set_accept_clicks(self, accept):
        # enable/disable user input
        self._accept_clicks = accept

    def heightForWidth(self, width):
        # keep square shape
        return width

    def hasHeightForWidth(self):
        return True

    def paintEvent(self, event):
        """
        draw grid, X/O marks, and highlight winner
        """
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            w, h = self.width(), self.height()
            side = min(w, h)
            offset_x, offset_y = (w-side)/2, (h-side)/2
            # background
            painter.fillRect(self.rect(), QColor("#333"))
            size = self.game_logic.board_size
            cell_size = side / size
            # grid lines
            pen = QPen(QColor("#555"), 2)
            painter.setPen(pen)
            for i in range(1, size):
                x = offset_x + i*cell_size
                painter.drawLine(int(x), int(offset_y), int(x), int(offset_y+side))
                y = offset_y + i*cell_size
                painter.drawLine(int(offset_x), int(y), int(offset_x+side), int(y))
            # draw marks
            for r in range(size):
                for c in range(size):
                    sym = self.game_logic.game_board[r][c]
                    if not sym: continue
                    cx = offset_x + c*cell_size + cell_size/2
                    cy = offset_y + r*cell_size + cell_size/2
                    rad = cell_size/2 * 0.7
                    if sym == 'X':
                        pen = QPen(QColor("#8acaff"), 4)
                        painter.setPen(pen)
                        # two crossing lines
                        painter.drawLine(QPointF(cx-rad, cy-rad), QPointF(cx+rad, cy+rad))
                        painter.drawLine(QPointF(cx+rad, cy-rad), QPointF(cx-rad, cy+rad))
                    else:
                        pen = QPen(QColor("#ff8a8a"), 4)
                        painter.setPen(pen)
                        painter.drawEllipse(QPointF(cx, cy), rad, rad)
            # if game over, draw winner in center
            if self.game_logic.game_over and self.game_logic.winner:
                win = self.game_logic.winner
                font = QFont("Arial", int(side*0.6), QFont.Bold)
                painter.setFont(font)
                color = QColor("#8acaff") if win=='X' else QColor("#ff8a8a")
                painter.setPen(QPen(color, 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                rect = QRect(int(offset_x), int(offset_y), int(side), int(side))
                painter.drawText(rect, Qt.AlignCenter, win)
        finally:
            pass  # nothing else

    def mouseReleaseEvent(self, event):
        """
        handle clicks: map coords to board cell and emit
        """
        if not self._accept_clicks or self.game_logic.game_over:
            return
        w, h = self.width(), self.height()
        side = min(w, h)
        ox, oy = (w-side)/2, (h-side)/2
        x, y = event.position().x(), event.position().y()
        # only inside grid
        if not (ox <= x < ox+side and oy <= y < oy+side):
            return
        size = self.game_logic.board_size
        cell = side / size
        if cell <= 0: return
        cx, cy = x-ox, y-oy
        col = int(cx//cell); row = int(cy//cell)
        # clamp to valid range
        row = max(0, min(row, size-1)); col = max(0, min(col, size-1))
        self.cell_clicked.emit(row, col)  # notify main window
