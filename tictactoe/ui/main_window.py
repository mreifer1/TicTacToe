import socket
from ..game_logic import GameLogic
from ..ui.board_widget import BoardWidget
from ..network import NetworkWorker

from PySide6.QtWidgets import (
    QMainWindow, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout,
    QPushButton, 
    QLabel, 
    QMenuBar, 
    QMenu, 
    QLineEdit, 
    QRadioButton,
    QGroupBox, 
    QMessageBox,
    QSizePolicy
)

from PySide6.QtGui import QAction, QFont
from PySide6.QtCore import Qt, QThread, Slot

class TicTacToeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_logic = GameLogic()
        self.board_widget = BoardWidget(self.game_logic, parent=self)
        self.network_thread = None; self.network_worker = None
        self.game_mode = "local"; self.my_symbol = 'X'; self.opponent_symbol = 'O'
        self.is_my_turn = True
        self.rematch_requested_by_me = False
        self.rematch_requested_by_opponent = False
        self.who_started_last_round = 'X'

        self._setup_ui()
        self._update_message("Select game mode or start local game.")

    def _setup_ui(self):
        self.setWindowTitle("Network Tic-Tac-Toe")
        self.setStyleSheet("""
            QMainWindow { background-color: #222; }
            QMenuBar { background-color: #333; color: #eee; }
            QMenuBar::item { color: #eee; }
            QMenuBar::item:selected { background-color: #555; }
            QMenu { background-color: #333; color: #eee; border: 1px solid #555; }
            QMenu::item { color: #eee; padding: 8px 20px; }
            QMenu::item:selected { background-color: #555; }
            QPushButton {
                background-color: #444;
                color: #eee;
                border: 1px solid #555;
                padding: 5px 10px;
                border-radius: 4px;
                min-height: 22px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #555; }
            QPushButton:disabled { background-color: #3a3a3a; color: #888; }
            QLabel { color: #eee; }
            QLineEdit { background-color: #555; color: #eee; border: 1px solid #777; border-radius: 3px; padding: 5px; }
            QRadioButton { color: #eee; }
            QGroupBox { color: #eee; border: 1px solid #555; margin-top: 10px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; background-color: #222; }
        """)
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self._create_menu_bar()
        self._create_network_controls()
        self.main_layout.addWidget(self.network_controls_group)
        self.main_layout.addWidget(self.board_widget, 1)
        self.board_widget.cell_clicked.connect(self._on_cell_clicked)
        self._create_bottom_controls()
        self.main_layout.addWidget(self.controls_bottom_widget)
        self._update_network_ui_state(enabled=True)
        self.board_widget.set_accept_clicks(True)
        self._update_rematch_buttons_visibility()

    def _create_menu_bar(self):
        menu_bar = QMenuBar(); game_menu = QMenu("Game", self)
        local_game_action = QAction("New Local Game", self); local_game_action.triggered.connect(self.reset_game)
        network_game_action = QAction("Setup Network Game", self); network_game_action.triggered.connect(self._enable_network_setup)
        quit_action = QAction("Quit", self); quit_action.triggered.connect(self.close)
        game_menu.addAction(local_game_action); game_menu.addAction(network_game_action); game_menu.addSeparator(); game_menu.addAction(quit_action)
        menu_bar.addMenu(game_menu); self.setMenuBar(menu_bar)

    def _create_network_controls(self):
        self.network_controls_group = QGroupBox("Network Game Setup")
        layout = QVBoxLayout()
        mode_layout = QHBoxLayout()
        self.host_radio = QRadioButton("Host Game"); self.client_radio = QRadioButton("Connect to Game")
        self.host_radio.setChecked(True); self.host_radio.toggled.connect(self._update_ip_input_state)
        mode_layout.addWidget(self.host_radio); mode_layout.addWidget(self.client_radio); mode_layout.addStretch()
        layout.addLayout(mode_layout)
        ip_layout = QHBoxLayout(); ip_layout.addWidget(QLabel("IP Address:"))
        self.ip_address_input = QLineEdit(); self.ip_address_input.setPlaceholderText("Your IP (auto-detect attempt)")
        detected_ip = self._get_local_ip();
        if detected_ip: self.ip_address_input.setText(detected_ip)
        self.ip_address_input.setEnabled(False)
        ip_layout.addWidget(self.ip_address_input); layout.addLayout(ip_layout)
        self.port = 9999
        self.start_network_button = QPushButton("Start Hosting")
        self.start_network_button.clicked.connect(self._start_or_connect_network_game)
        layout.addWidget(self.start_network_button, alignment=Qt.AlignCenter)
        self.network_controls_group.setLayout(layout)

    def _get_local_ip(self):
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(0.1); s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
            if ip == '127.0.0.1':
                hostname = socket.gethostname(); ip = socket.gethostbyname(hostname)
            return ip
        except Exception: return None
        finally:
            if s: s.close()

    def _update_ip_input_state(self):
        is_client = self.client_radio.isChecked()
        self.ip_address_input.setEnabled(is_client)
        self.ip_address_input.setPlaceholderText("Enter Host IP to Connect" if is_client else "Your IP (optional, will try auto-detect)")
        self.start_network_button.setText("Connect to Host" if is_client else "Start Hosting")
        if not is_client:
            detected_ip = self._get_local_ip(); self.ip_address_input.setText(detected_ip if detected_ip else "")
        else: self.ip_address_input.setText("")

    def _create_bottom_controls(self):
        self.controls_bottom_widget = QWidget(); self.bottom_layout = QHBoxLayout(self.controls_bottom_widget)
        self.controls_bottom_widget.setStyleSheet("background-color: transparent;")

        self.message_label = QLabel(""); font = QFont(); font.setPointSize(12); self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.message_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.message_label.setWordWrap(True)

        self.reset_button = QPushButton("Reset"); self.reset_button.clicked.connect(self.reset_game)
        self.rematch_button = QPushButton("Rematch?"); self.rematch_button.clicked.connect(self._request_rematch)
        self.accept_rematch_button = QPushButton("Accept"); self.accept_rematch_button.clicked.connect(self._accept_rematch)
        self.decline_rematch_button = QPushButton("Decline"); self.decline_rematch_button.clicked.connect(self._decline_rematch)

        self.bottom_layout.addWidget(self.message_label)
        self.bottom_layout.addStretch(1)
        self.bottom_layout.addWidget(self.rematch_button)
        self.bottom_layout.addWidget(self.accept_rematch_button)
        self.bottom_layout.addWidget(self.decline_rematch_button)
        self.bottom_layout.addWidget(self.reset_button)

    def _update_rematch_buttons_visibility(self):
        is_net_game_over = self.game_mode in ["host", "client"] and self.game_logic.game_over

        show_request = is_net_game_over and not self.rematch_requested_by_me and not self.rematch_requested_by_opponent
        show_accept_decline = is_net_game_over and self.rematch_requested_by_opponent

        self.rematch_button.setVisible(show_request)
        self.rematch_button.setEnabled(show_request)

        self.accept_rematch_button.setVisible(show_accept_decline)
        self.decline_rematch_button.setVisible(show_accept_decline)

        self.reset_button.setEnabled(not self.rematch_requested_by_me and not self.rematch_requested_by_opponent)


    @Slot(str)
    def _update_message(self, message, is_error=False, is_success=False, is_turn=False):
        style = "color: #eee;";
        if is_error: style = "color: #ff8a8a; font-weight: bold;"
        elif is_success: style = "color: lime; font-weight: bold;"
        elif is_turn: style = "color: #8acaff; font-weight: bold;"
        self.message_label.setStyleSheet(style); self.message_label.setText(message)

    def _update_network_ui_state(self, enabled): self.network_controls_group.setEnabled(enabled)
    def _enable_network_setup(self): self.reset_game(); self._update_network_ui_state(enabled=True); self._update_message("Setup network game.")

    @Slot()
    def _start_or_connect_network_game(self):
        if self.network_thread and self.network_thread.isRunning(): self._update_message("Network active.", is_error=True); return
        self._stop_network_worker()
        ip_address = self.ip_address_input.text().strip(); is_hosting = self.host_radio.isChecked()
        if is_hosting:
            self.game_mode = "host"; host_ip = ip_address if ip_address else self._get_local_ip()
            if not host_ip or host_ip == '127.0.0.1':
                 detected_ip = self._get_local_ip()
                 if detected_ip and detected_ip != '127.0.0.1': host_ip = detected_ip
                 elif ip_address and ip_address != '127.0.0.1': host_ip = ip_address
                 else: QMessageBox.warning(self, "Network Error", "Could not determine valid host IP. Please enter your network IP manually."); return
            self.ip_address_input.setText(host_ip); self._setup_and_start_worker()
            self.network_worker.start_hosting(host_ip, self.port)
        else:
            self.game_mode = "client"
            if not ip_address: QMessageBox.warning(self, "Network Error", "Please enter host IP."); return
            self._setup_and_start_worker()
            self.network_worker.start_connecting(ip_address, self.port)
        self._update_network_ui_state(enabled=False); self.board_widget.set_accept_clicks(False)
        self.who_started_last_round = 'X'

    def _setup_and_start_worker(self):
        self.network_thread = QThread(self); self.network_worker = NetworkWorker()
        self.network_worker.moveToThread(self.network_thread)
        self.network_worker.connected.connect(self._on_network_connected)
        self.network_worker.disconnected.connect(self._on_network_disconnected)
        self.network_worker.move_received.connect(self._on_move_received)
        self.network_worker.status_update.connect(self._on_status_update)
        self.network_worker.error_occurred.connect(self._on_network_error)
        self.network_worker.assign_player_symbol.connect(self._on_assign_symbol)
        self.network_worker.rematch_request_received.connect(self._handle_rematch_request)
        self.network_worker.rematch_accepted.connect(self._handle_rematch_accepted)
        self.network_worker.rematch_declined.connect(self._handle_rematch_declined)
        self.network_thread.started.connect(lambda: print("Network thread started."))
        self.network_thread.finished.connect(self._on_network_thread_finished)
        self.network_thread.finished.connect(self.network_worker.deleteLater)
        self.network_thread.start()

    @Slot(str)
    def _on_assign_symbol(self, symbol):
        self.my_symbol = symbol; self.opponent_symbol = 'O' if symbol == 'X' else 'X'
        self._update_message(f"Network game started. You are '{self.my_symbol}'.")
        self.is_my_turn = (self.my_symbol == self.who_started_last_round)
        self.board_widget.set_accept_clicks(self.is_my_turn)
        if not self.is_my_turn: self._update_message(f"Waiting for opponent ('{self.opponent_symbol}')'s move...", is_turn=False)
        else: self._update_message(f"Your ({self.my_symbol}) turn.", is_turn=True)
        self._update_rematch_buttons_visibility()


    @Slot()
    def _on_network_connected(self): pass

    @Slot(str)
    def _on_network_disconnected(self, reason):
        if self.game_mode != "local":
            self._update_message(f"Disconnected: {reason}", is_error=True)
            if not hasattr(self, '_reset_in_progress') or not self._reset_in_progress:
                 QMessageBox.information(self, "Disconnected", f"Network connection closed: {reason}")
            self.reset_game()

    @Slot(str)
    def _on_network_error(self, error_message):
        if self.game_mode != "local" and (not hasattr(self, '_reset_in_progress') or not self._reset_in_progress):
             self._update_message(f"Network Error: {error_message}", is_error=True)
             QMessageBox.critical(self, "Network Error", error_message)
             self._stop_network_worker(); self._update_network_ui_state(enabled=True)
             self.game_mode = "local"; self.is_my_turn = True; self.board_widget.set_accept_clicks(True)
             self._update_rematch_buttons_visibility()

    @Slot(str)
    def _on_status_update(self, status):
        if not hasattr(self, '_reset_in_progress') or not self._reset_in_progress:
             self._update_message(status)

    @Slot()
    def _on_network_thread_finished(self):
        print("Network thread finished.")
        self.network_thread = None; self.network_worker = None
        if self.game_mode != "local" and not self.game_logic.game_over and \
           (not hasattr(self, '_reset_in_progress') or not self._reset_in_progress):
             self._update_message("Network connection ended unexpectedly.", is_error=True)
             self._update_rematch_buttons_visibility()

    def _handle_game_over(self, message, is_success):
        self._update_message(message, is_success=is_success, is_error=not is_success)
        self.board_widget.set_accept_clicks(False)
        self.is_my_turn = False
        self._update_rematch_buttons_visibility()


    @Slot(int, int)
    def _on_cell_clicked(self, row, col):
        if self.game_logic.game_over: return

        if self.game_mode == "local":
            player_to_move = 'X' if self.game_logic.move_count % 2 == 0 else 'O'
            result = self.game_logic.make_move(row, col, player_to_move)
            if result != "invalid":
                self.board_widget.update()
                if result == "win": self._handle_game_over(f"Player {self.game_logic.winner} wins!", True)
                elif result == "draw": self._handle_game_over("It's a draw!", True)
                else: next_player = 'X' if self.game_logic.move_count % 2 == 0 else 'O'; self._update_message(f"Player {next_player}'s turn")
        elif self.game_mode in ["host", "client"]:
            if not self.is_my_turn: self._update_message("Wait! It's not your turn.", is_error=True); return
            if self.game_logic.is_cell_empty(row, col):
                result = self.game_logic.make_move(row, col, self.my_symbol); self.board_widget.update()
                if self.network_worker and self.network_worker._running: self.network_worker.send_move(row, col)
                else: print("Warning: Cannot send move, network worker not active."); self._update_message("Network inactive.", is_error=True); self.reset_game(); return

                if result == "win": self._handle_game_over(f"You ({self.my_symbol}) win!", True)
                elif result == "draw": self._handle_game_over("It's a draw!", True)
                elif result == "continue": self.is_my_turn = False; self.board_widget.set_accept_clicks(False); self._update_message(f"Waiting for opponent ('{self.opponent_symbol}')'s move...")
            else: self._update_message("Cell already taken.", is_error=True)

    @Slot(int, int)
    def _on_move_received(self, row, col):
        if self.game_logic.game_over or self.game_mode == "local": return
        result = self.game_logic.make_move(row, col, self.opponent_symbol); self.board_widget.update()
        if result == "win": self._handle_game_over(f"Opponent ({self.opponent_symbol}) wins!", False)
        elif result == "draw": self._handle_game_over("It's a draw!", True)
        elif result == "continue": self.is_my_turn = True; self.board_widget.set_accept_clicks(True); self._update_message(f"Your ({self.my_symbol}) turn.", is_turn=True)
        elif result == "invalid": print(f"[Warning] Received invalid move ({row},{col}) from opponent."); self._update_message(f"Received invalid move? Your ({self.my_symbol}) turn.", is_error=True); self.is_my_turn = True; self.board_widget.set_accept_clicks(True)

    @Slot()
    def _request_rematch(self):
        if self.network_worker and self.network_worker._running:
            self.network_worker.send_rematch_request()
            self.rematch_requested_by_me = True
            self._update_message("Rematch requested, waiting for opponent...")
            self._update_rematch_buttons_visibility()

    @Slot()
    def _accept_rematch(self):
        if self.network_worker and self.network_worker._running:
            self.network_worker.send_rematch_accept()
            self._start_new_round()

    @Slot()
    def _decline_rematch(self):
        if self.network_worker and self.network_worker._running:
            self.network_worker.send_rematch_decline()
            self.rematch_requested_by_opponent = False
            self._update_message("Rematch declined. Game Over.")
            self._update_rematch_buttons_visibility()

    @Slot()
    def _handle_rematch_request(self):
        if self.game_logic.game_over:
            self.rematch_requested_by_opponent = True
            self._update_message("Opponent requests a rematch!")
            self._update_rematch_buttons_visibility()

    @Slot()
    def _handle_rematch_accepted(self):
        if self.rematch_requested_by_me:
            self._update_message("Rematch accepted!")
            self._start_new_round()

    @Slot()
    def _handle_rematch_declined(self):
        if self.rematch_requested_by_me:
            self.rematch_requested_by_me = False
            self._update_message("Opponent declined rematch. Game Over.")
            self._update_rematch_buttons_visibility()

    def _start_new_round(self):
        print("Starting new round...")
        self.game_logic.reset_game()
        self.rematch_requested_by_me = False
        self.rematch_requested_by_opponent = False

        self.who_started_last_round = 'O' if self.who_started_last_round == 'X' else 'X'
        self.is_my_turn = (self.my_symbol == self.who_started_last_round)

        self.board_widget.set_accept_clicks(self.is_my_turn)
        self.board_widget.update()
        self._update_rematch_buttons_visibility()

        if self.is_my_turn:
            self._update_message(f"New round! Your ({self.my_symbol}) turn.", is_turn=True)
        else:
            self._update_message(f"New round! Waiting for opponent ('{self.opponent_symbol}')'s move...")


    def _stop_network_worker(self):
        print("Stopping network worker...")
        self._explicit_stop = True
        if self.network_worker:
             try: self.network_worker.stop()
             except RuntimeError: print("Worker likely already deleted.")
        if self.network_thread and self.network_thread.isRunning():
            self.network_thread.quit()
            if not self.network_thread.wait(1000): print("Warning: Network thread termination required."); self.network_thread.terminate()
        self.network_thread = None; self.network_worker = None
        self._explicit_stop = False
        print("Network worker stopped.")

    @Slot()
    def reset_game(self):
        print("Resetting game..."); self._reset_in_progress = True
        self._stop_network_worker()
        self.game_logic.reset_game(); self.game_mode = "local"; self.my_symbol = 'X'; self.opponent_symbol = 'O'; self.is_my_turn = True
        self.rematch_requested_by_me = False
        self.rematch_requested_by_opponent = False
        self.who_started_last_round = 'X'
        self._update_message("New local game. Player X's turn."); self.message_label.setStyleSheet("")
        self.board_widget.set_accept_clicks(True); self.board_widget.update(); self._update_network_ui_state(enabled=True)
        self._update_rematch_buttons_visibility()
        self._reset_in_progress = False

    def closeEvent(self, event):
        self._stop_network_worker(); event.accept()
