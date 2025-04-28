class GameLogic:
    """
    tic-tac-toe rules and state
    """
    def __init__(self):
        """
        init board and counters
        """
        self.board_size = 3               # fixed 3x3 grid
        self.game_board = [['' for _ in range(self.board_size)]
                           for _ in range(self.board_size)]  # empty cells
        self.game_over = False            # flag when win/draw
        self.winner = None                # 'X', 'O', or None
        self.move_count = 0               # how many moves done

    def make_move(self, row, col, player):
        """
        place player mark, check result
        returns: 'win', 'draw', 'continue', or 'invalid'
        """
        # only if cell empty and game not over
        if not self.game_over and 0 <= row < self.board_size \
           and 0 <= col < self.board_size \
           and self.game_board[row][col] == '':
            self.game_board[row][col] = player
            self.move_count += 1           # count this move
            if self.check_win(player):
                self.game_over = True; self.winner = player
                return "win"
            elif self.check_draw():
                self.game_over = True; self.winner = None
                return "draw"
            return "continue"
        return "invalid"

    def check_win(self, player):
        """
        scan rows, cols, diags for 3 in a row
        """
        b = self.game_board; n = self.board_size
        # rows and cols
        for i in range(n):
            if all(b[i][j] == player for j in range(n)) \
               or all(b[j][i] == player for j in range(n)):
                return True
        # main diag
        if all(b[i][i] == player for i in range(n)):
            return True
        # anti-diag
        if all(b[i][n - 1 - i] == player for i in range(n)):
            return True
        return False

    def check_draw(self):
        """
        no empty cells and no winner
        """
        # full board and not already won
        return self.move_count == self.board_size * self.board_size \
               and not self.winner

    def is_cell_empty(self, row, col):
        """
        true if coords valid and cell blank
        """
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return self.game_board[row][col] == ''
        return False

    def reset_game(self):
        """
        clear board and reset flags
        """
        # back to fresh state
        self.game_board = [['' for _ in range(self.board_size)]
                           for _ in range(self.board_size)]
        self.game_over = False; self.winner = None; self.move_count = 0
