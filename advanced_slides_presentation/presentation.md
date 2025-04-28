---
theme: consult
highlightTheme: css/vs2015.css
timeForPresentation: "600"
---

# Network Tic-Tac-Toe: A Deep Dive

Exploring the Networking, GUI, and Game Logic

---

## Project Overview

- A classic Tic-Tac-Toe game playable over a local network.
- Built using Python with:
  - **PySide6 (Qt6):** For the Graphical User Interface (GUI).
  - **`socket` module:** For TCP/IP network communication.
  - **`threading` module:** To keep the GUI responsive during network operations.
- Clear separation between:
  - Networking (`NetworkWorker`)
  - User Interface (`TicTacToeWindow`, `BoardWidget`)
  - Game Rules (`GameLogic`)

---

## Part 1: Networking

How two players connect and exchange moves.

---

### Networking Model

- **Client-Server Architecture:**
  - One player **Hosts** the game (acts as the server).
  - The other player **Connects** to the host (acts as the client).
- **TCP/IP Communication:**
  - Uses standard Python `socket` library. Reliable, ordered data stream.
- **Dedicated Network Handler:**
  - Logic is encapsulated in the `NetworkWorker` class.

---

### The `NetworkWorker` Class

- **Responsibilities:** Handles all socket operations: creation, binding, listening, connecting, sending, receiving.
- **Threading:** Runs its core blocking operations (`accept`, `connect`, `recv`) in a separate Python `threading.Thread`.
  - This prevents the main GUI thread from freezing during network waits.
- **GUI Communication:** Uses Qt Signals (`connected`, `disconnected`, `move_received`, `status_update`, etc.) to safely communicate events *back* to the `TicTacToeWindow` in the main thread.

--

```python
# Runs its network loops in a separate thread
class NetworkWorker(QObject): # Inherits from QObject for signals/slots
    # Signals emitted to notify the main GUI thread
    connected = Signal()
    disconnected = Signal(str)
    move_received = Signal(int, int)
    status_update = Signal(str)
    error_occurred = Signal(str)
    assign_player_symbol = Signal(str)
    rematch_request_received = Signal()
    # ... other signals ...

    def __init__(self):
        super().__init__()
        self.socket = None         # Active connection socket
        self.server_socket = None  # Listening socket (for host)
        # ... other attributes ...
        self._running = False      # Flag to control thread loops
        self.connection_thread = None

    # ... methods to start/stop/send/receive ...
````

---

### Starting the Connection

- Initiated by the `TicTacToeWindow` based on user input.
- Two main paths, triggered via `@Slot` decorators in `NetworkWorker`:

1. **Hosting (`start_hosting`):** Waits for an incoming connection.
2. **Connecting (`start_connecting`):** Actively tries to connect to a host.

--

```python
class NetworkWorker(QObject):
    # ... signals ...

    # Slot connected to a signal from the main window
    @Slot(str, int) # Expects IP (str) and port (int)
    def start_hosting(self, host_ip, port):
        self.host_ip = host_ip; self.port = port; self.is_hosting = True
        # Starts _host_thread_func in a new thread
        self._start_connection_thread(self._host_thread_func, ())

    # Slot connected to a signal from the main window
    @Slot(str, int) # Expects IP (str) and port (int)
    def start_connecting(self, host_ip, port):
        self.host_ip = host_ip; self.port = port; self.is_hosting = False
        # Starts _connect_thread_func in a new thread
        self._start_connection_thread(self._connect_thread_func, ())

    def _start_connection_thread(self, target_func, args_tuple):
        # Manages the creation and start of the network thread
        if self.connection_thread and self.connection_thread.is_alive(): return
        self._running = True
        # Uses Python's standard threading
        self.connection_thread = threading.Thread(target=target_func, args=args_tuple, daemon=True)
        self.connection_thread.start()
```

---

### Hosting Logic (`_host_thread_func`)

- **Runs in the network thread.**

1. Creates a server socket (`socket.socket`).
2. Sets `SO_REUSEADDR` option (allows restarting server quickly).
3. Binds to the host IP and port (`server_socket.bind`).
4. Listens for one incoming connection (`server_socket.listen(1)`).
5. Emits `status_update` signal ("Listening...").
6. Enters a loop calling `server_socket.accept()` (blocks with timeout until a client connects or `_running` is false).
7. Once connected:
    - Stores the client socket (`self.socket`).
    - Emits `status_update` ("Opponent connected...").
    - Emits `assign_player_symbol('X')`. Host is always 'X'.
    - Emits `connected`.
    - Calls `_handle_connection` to manage ongoing communication.

- Includes error handling (`try...except`) and cleanup.

---

### Connecting Logic (`_connect_thread_func`)

- **Runs in the network thread.**

1. Creates a client socket (`socket.socket`).
2. Emits `status_update` ("Connecting...").
3. Attempts to connect to the specified host IP and port (`client_socket.connect`). Uses a timeout.
4. If successful:
    - Stores the server socket (`self.socket`).
    - Emits `status_update` ("Connected to host.").
    - Emits `assign_player_symbol('O')`. Client is always 'O'.
    - Emits `connected`.
    - Calls `_handle_connection` to manage ongoing communication.

- Includes error handling for timeouts, address errors, connection refused, etc.

---

### Sending Data (`send_move`, `_send_message`)

- Called from the **main GUI thread** (indirectly via user click).
- `send_move(row, col)`: Formats the move as a string (e.g., `"1,2"`).
- `_send_message(message)`:
    1. Checks if the socket exists and the worker is running.
    2. Encodes the string message to bytes (`utf-8`).
    3. Sends all bytes over the socket using `socket.sendall()`.
    4. Handles potential `socket.error` during sending, emits `disconnected` if failure occurs.
- Special messages (rematch requests/responses) use a prefix (`NET::`) and are sent via dedicated methods (`send_rematch_request`, etc.) which also call `_send_message`.

--

```python
class NetworkWorker(QObject):
    # ... other methods ...
    @Slot(int, int) # Called by TicTacToeWindow
    def send_move(self, row, col):
        move_str = f"{row},{col}" # Format as string
        self._send_message(move_str)

    # Internal helper
    def _send_message(self, message):
        if self.socket and self._running:
            try:
                # Encode string to bytes and send
                self.socket.sendall(message.encode('utf-8'))
                return True
            except socket.error as e:
                # Handle errors, potentially emit disconnected signal
                # ... error handling ...
                return False
```

---

### Receiving Data (`_handle_connection`)

- **Runs continuously in the network thread** after a connection is established.
- **Main Loop:**
    1. Blocks on `socket.recv(1024)`, waiting for data.
    2. If `recv` returns empty data: Opponent disconnected cleanly. Emit `disconnected` signal, stop the loop.
    3. If data received: Decode bytes to string (`utf-8`).
    4. **Parse Message:**
        - If starts with `NET::`: Handle network command (e.g., `REQ_REMATCH`), emit corresponding signal (`rematch_request_received`).
        - Else (assume it's a move): Split string by comma (e.g., `"1,2"` -> `['1', '2']`). Convert parts to integers `row`, `col`. Emit `move_received(row, col)`.
    5. Handles potential errors (`ConnectionResetError`, `socket.error`, `ValueError`) during receive/parse, emits `disconnected`, stops loop.
- **Cleanup:** Closes the socket when the loop ends.

---

## Part 2: The User Interface (PySide6)

How the game looks and how the user interacts with it.

---

### What is PySide6?

- Official Python bindings for the **Qt framework**.
- Qt is a mature, cross-platform C++ framework for developing applications with GUIs, but also networking, threading, databases, etc.
- **Key Concepts Used:**
    - **Widgets:** UI elements (Window, Button, Label, Layouts). `QMainWindow`, `QWidget`, `QPushButton`, `QLabel`, `QLineEdit`, `QGroupBox`.
    - **Layouts:** Arrange widgets (`QVBoxLayout`, `QHBoxLayout`).
    - **Signals & Slots:** The core mechanism for communication between objects (especially across threads). Decoupled event handling.
    - **Event Loop:** Processes user input, signals, timers, etc. Keeps the GUI responsive. `QApplication.exec()`.
    - **`QPainter`:** Used in `BoardWidget` for custom 2D drawing (lines, circles, text).

---

### The Main Window (`TicTacToeWindow`)

- Inherits from `QMainWindow`.
- **Orchestrator:** Ties everything together.
    - Creates instances of `GameLogic` and `BoardWidget`.
    - Creates the `NetworkWorker` and manages its `QThread`.
    - Sets up the UI: menu bar, network control group, board widget, status label, buttons.
    - Connects signals from UI elements (button clicks, menu actions), `BoardWidget`, and `NetworkWorker` to its own **slots** (methods).
- **State Management:** Tracks `game_mode` (local/host/client), `my_symbol`, `is_my_turn`, rematch status.
- **Slots:** Methods decorated with `@Slot` (or connected directly) that react to signals. Examples:
    - `_on_cell_clicked`: Handles clicks on the board.
    - `_on_move_received`: Handles moves from the network.
    - `_on_network_disconnected`: Handles network disconnects.
    - `reset_game`: Resets the game state and UI.
    - `_start_or_connect_network_game`: Initiates network setup.

---

### Drawing the Board (`BoardWidget`)

- Inherits from `QWidget`.
- **Custom Drawing:** Overrides the `paintEvent` method.
    - Uses `QPainter` to draw the UI.
    - Calculates cell sizes based on widget dimensions.
    - Draws the grid lines.
    - Iterates through `self.game_logic.game_board` and draws 'X' (lines) or 'O' (ellipse) in occupied cells using different colors.
    - Uses `painter.drawText` to overlay the winner ('X' or 'O') when the game is over.
- **Click Handling:** Overrides `mouseReleaseEvent`.
    - Calculates which cell (row, col) was clicked based on coordinates.
    - Emits the `cell_clicked(row, col)` signal if the click is valid and clicks are accepted.
- **Responsive:** `hasHeightForWidth` and `heightForWidth` ensure it tries to stay square. `QSizePolicy.Ignored` allows it to fill available space.

--

Python

```
class BoardWidget(QWidget):
    cell_clicked = Signal(int, int) # Signal emitted on valid click

    def __init__(self, game_logic, parent=None):
        # ... setup ...
        self.game_logic = game_logic # Reference to check board state

    def paintEvent(self, event):
        painter = QPainter(self)
        # ... calculate sizes ...
        # Draw grid lines
        # Loop through self.game_logic.game_board:
            # Draw 'X' or 'O' using painter.drawLine / painter.drawEllipse
        # If game over, draw winner text
        # ... cleanup painter ...

    def mouseReleaseEvent(self, event):
        # ... calculate row, col from event.position() ...
        # If valid click:
        self.cell_clicked.emit(row, col)
```

---

### UI Interaction: Signals & Slots

- The **foundation** of Qt's (and PySide6's) event handling.
- **Decoupling:** Objects don't need direct references to call methods on each other. They just emit signals. Other objects connect their slots to those signals.
- **Example Flow (Click):**
    1. User clicks the `BoardWidget`.
    2. `BoardWidget.mouseReleaseEvent` detects click, calculates `row, col`.
    3. `BoardWidget` emits `cell_clicked(row, col)`.
    4. `TicTacToeWindow._on_cell_clicked` (which was connected to `cell_clicked`) is executed.
- **Example Flow (Network Receive):**
    1. `NetworkWorker._handle_connection` receives data, parses move `row, col`.
    2. `NetworkWorker` emits `move_received(row, col)`.
    3. `TicTacToeWindow._on_move_received` (connected to `move_received`) is executed.
- **Thread Safety:** Signals emitted from the `NetworkWorker`'s thread are automatically queued and executed safely in the main GUI thread's event loop, allowing safe UI updates.

---

## Part 3: Game Logic

The rules of Tic-Tac-Toe, independent of UI or Network.

---

### The `GameLogic` Class

- **Pure Python:** Contains only the rules and state of the Tic-Tac-Toe game. No PySide6 or socket code.
- **Responsibilities:**
    - Maintain the game board state (3x3 list of lists: `game_board`).
    - Validate player moves (`make_move`).
    - Check for win conditions (`check_win`).
    - Check for draw conditions (`check_draw`).
    - Reset the board for a new game (`reset_game`).
    - Track move count (`move_count`).
- **State Variables:**
    - `game_board`: The 3x3 grid.
    - `game_over`: Boolean flag.
    - `winner`: Stores 'X', 'O', or `None`.
    - `move_count`: Number of moves made.

--

Python

```
class GameLogic:
    def __init__(self):
        self.board_size = 3
        self.game_board = [['' for _ in range(self.board_size)] # 3x3 grid
                            for _ in range(self.board_size)]
        self.game_over = False
        self.winner = None
        self.move_count = 0

    def make_move(self, row, col, player):
        # Checks if move is valid (in bounds, cell empty, game not over)
        # Updates self.game_board[row][col] = player
        # Increments self.move_count
        # Calls self.check_win() and self.check_draw()
        # Updates self.game_over and self.winner
        # Returns status ("win", "draw", "continue", "invalid")

    def check_win(self, player):
        # Checks rows, columns, and diagonals for 3-in-a-row for 'player'
        # Returns True if win, False otherwise

    def check_draw(self):
        # Returns True if move_count == 9 and no winner

    def reset_game(self):
        # Resets board, game_over, winner, move_count
```

---

## Part 4: Tying It All Together

How Networking, GUI, and Logic collaborate.

---

### Interaction Flow: Making a Local Move

1. **User:** Clicks a cell on the `BoardWidget`.
2. **`BoardWidget`:** `mouseReleaseEvent` -> Calculates `row, col` -> Emits `cell_clicked(row, col)`.
3. **`TicTacToeWindow`:** Slot `_on_cell_clicked(row, col)` is triggered.
4. **`TicTacToeWindow`:** Determines current player ('X' or 'O').
5. **`TicTacToeWindow`:** Calls `self.game_logic.make_move(row, col, player)`.
6. **`GameLogic`:** Validates move, updates `game_board`, checks for win/draw, updates `game_over`/`winner`, returns status ("win", "draw", "continue").
7. **`TicTacToeWindow`:** Checks returned status.
8. **`TicTacToeWindow`:** Calls `self.board_widget.update()` to trigger a repaint.
9. **`BoardWidget`:** `paintEvent` reads updated `game_logic.game_board` and redraws.
10. **`TicTacToeWindow`:** Updates `message_label` (e.g., "Player O's turn", "Player X Wins!"). Updates button states if game over.

---

### Interaction Flow: Making a Network Move (Sending)

_(Assumes network game is active, it's My Turn)_

1. **User:** Clicks a cell on `BoardWidget`.
2. **`BoardWidget`:** Emits `cell_clicked(row, col)`.
3. **`TicTacToeWindow`:** `_on_cell_clicked` runs.
4. **`TicTacToeWindow`:** Checks `self.is_my_turn`. It's True.
5. **`TicTacToeWindow`:** Calls `self.game_logic.make_move(row, col, self.my_symbol)`.
6. **`GameLogic`:** Updates board, checks win/draw.
7. **`TicTacToeWindow`:** Calls `self.board_widget.update()`.
8. **`BoardWidget`:** Repaints with the new move.
9. **`TicTacToeWindow`:** **Crucially**, calls `self.network_worker.send_move(row, col)`.
10. **`NetworkWorker`:** (In main thread) `send_move` slot -> `_send_message` -> encodes `"row,col"` -> `socket.sendall()`.
11. **`TicTacToeWindow`:** Updates status ("Waiting for opponent...") and sets `self.is_my_turn = False`, disables board clicks. Updates buttons if game over.

---

### Interaction Flow: Receiving a Network Move

_(Assumes network game is active, it's Opponent's Turn)_

1. **Network:** Data arrives on the socket.
2. **`NetworkWorker`:** (In network thread) `_handle_connection` loop -> `socket.recv()` gets data.
3. **`NetworkWorker`:** Decodes bytes to string (e.g., `"1,2"`).
4. **`NetworkWorker`:** Parses string -> `row=1`, `col=2`.
5. **`NetworkWorker`:** Emits `move_received(row, col)` signal.
6. **`TicTacToeWindow`:** (In main GUI thread) Slot `_on_move_received(row, col)` is triggered by the signal.
7. **`TicTacToeWindow`:** Calls `self.game_logic.make_move(row, col, self.opponent_symbol)`.
8. **`GameLogic`:** Updates board, checks win/draw.
9. **`TicTacToeWindow`:** Calls `self.board_widget.update()`.
10. **`BoardWidget`:** Repaints with the opponent's move.
11. **`TicTacToeWindow`:** Updates status ("Your turn.") and sets `self.is_my_turn = True`, enables board clicks. Updates buttons if game over.

---

### Cleanup

- **`NetworkWorker.stop()`:**
    - Sets `_running = False` to break thread loops.
    - Tries to `shutdown` and `close` both client and server sockets gracefully.
    - Called by `TicTacToeWindow`.
- **`TicTacToeWindow.closeEvent()`:**
    - Overridden method automatically called when the window is closed.
    - Ensures `_stop_network_worker()` is called to clean up the network thread and sockets before the application exits.
- **`TicTacToeWindow.reset_game()`:**
    - Calls `_stop_network_worker()` to end any existing network connection.
    - Resets `GameLogic`.
    - Resets UI state to local game mode.

---

## TLDR / Summary

- **Modular Design:** Networking, GUI, and Game Logic are well-separated.
- **PySide6 GUI:** Uses widgets, layouts, `QPainter` for drawing, and the crucial signal/slot mechanism.
- **`GameLogic`:** Pure Python class holding game state and rules.
- **`NetworkWorker`:** Handles `socket` communication in a separate `threading.Thread` to avoid blocking the GUI.
- **Signals/Slots:** Enable safe cross-thread communication (Network -> GUI) and decouple components within the GUI (Board -> Window).
- **TCP/IP:** Used for reliable move and command exchange between host and client.

---

## Full Code Reference

```python
import sys
import socket
import threading
# ... (rest of the imports) ...

NET_MSG_PREFIX = "NET::"
# ... (rest of constants) ...

class GameLogic:
    # ... (GameLogic code as provided) ...

class NetworkWorker(QObject):
    # ... (NetworkWorker code as provided) ...

class BoardWidget(QWidget):
    # ... (BoardWidget code as provided) ...

class TicTacToeWindow(QMainWindow):
    # ... (TicTacToeWindow code as provided) ...

if __name__ == "__main__":
    # ... (Application setup and execution code as provided) ...
```