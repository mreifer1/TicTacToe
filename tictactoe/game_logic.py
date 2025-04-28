class GameLogic:
    def __init__(self):
        self.board_size = 3
        self.game_board = [['' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.game_over = False
        self.winner = None
        self.move_count = 0

    def make_move(self, row, col, player):
        if not self.game_over and 0 <= row < self.board_size and 0 <= col < self.board_size and self.game_board[row][col] == '':
            self.game_board[row][col] = player
            self.move_count += 1
            if self.check_win(player):
                self.game_over = True; self.winner = player; return "win"
            elif self.check_draw():
                self.game_over = True; self.winner = None; return "draw"
            return "continue"
        return "invalid"

    def check_win(self, player):
        board = self.game_board; size = self.board_size
        for i in range(size):
            if all(board[i][j] == player for j in range(size)) or \
               all(board[j][i] == player for j in range(size)): return True
        if all(board[i][i] == player for i in range(size)) or \
           all(board[i][size - 1 - i] == player for i in range(size)): return True
        return False

    def check_draw(self):
        return self.move_count == self.board_size * self.board_size and not self.winner

    def is_cell_empty(self, row, col):
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return self.game_board[row][col] == ''
        return False

    def reset_game(self):
        self.game_board = [['' for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.game_over = False; self.winner = None; self.move_count = 0
