import socket
from ..game_logic import GameLogic
from ..ui.board_widget import BoardWidget
from ..network import NetworkWorker

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMenuBar, QMenu, QLineEdit,
    QRadioButton, QGroupBox, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QAction, QFont
from PySide6.QtCore import Qt, QThread, Slot

class TicTacToeWindow(QMainWindow):
    """
    main window UI and game flow
    """
    def __init__(self):
        """
        init state, ui widgets, signals
        """
        super().__init__()
        self.game_logic = GameLogic()
        self.board_widget = BoardWidget(self.game_logic, parent=self)
        # network thread + worker placeholders
        self.network_thread = None; self.network_worker = None
        # game state flags
        self.game_mode = "local"; self.my_symbol = 'X'; self.opponent_symbol = 'O'
        self.is_my_turn = True
        self.rematch_requested_by_me = False
        self.rematch_requested_by_opponent = False
        self.who_started_last_round = 'X'

        self._setup_ui()
        self._update_message("Select game mode or start local game.")

    def _setup_ui(self):
        '''window look + layout'''
        self.setWindowTitle("Network Tic-Tac-Toe")
        self.setStyleSheet("""
            QMainWindow { background-color: #222; }
            ...
        """)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._create_menu_bar()            # top menu
        self._create_network_controls()    # host/connect ui
        self.main_layout.addWidget(self.network_controls_group)
        self.main_layout.addWidget(self.board_widget, 1)
        self.board_widget.cell_clicked.connect(self._on_cell_clicked)

        self._create_bottom_controls()     # status + buttons
        self.main_layout.addWidget(self.controls_bottom_widget)
        self._update_network_ui_state(enabled=True)
        self.board_widget.set_accept_clicks(True)
        self._update_rematch_buttons_visibility()

    def _create_menu_bar(self):
        '''file/game menu actions'''
        menu_bar = QMenuBar()
        game_menu = QMenu("Game", self)
        local_action = QAction("New Local Game", self)
        local_action.triggered.connect(self.reset_game)
        net_action = QAction("Setup Network Game", self)
        net_action.triggered.connect(self._enable_network_setup)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        for act in (local_action, net_action): game_menu.addAction(act)
        game_menu.addSeparator(); game_menu.addAction(quit_action)
        menu_bar.addMenu(game_menu)
        self.setMenuBar(menu_bar)

    def _create_network_controls(self):
        '''network setup group'''
        self.network_controls_group = QGroupBox("Network Game Setup")
        layout = QVBoxLayout()
        mode_layout = QHBoxLayout()
        self.host_radio = QRadioButton("Host Game")
        self.client_radio = QRadioButton("Connect to Game")
        self.host_radio.setChecked(True)
        self.host_radio.toggled.connect(self._update_ip_input_state)
        mode_layout.addWidget(self.host_radio)
        mode_layout.addWidget(self.client_radio)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        # ip + port input
        ip_layout = QHBoxLayout(); ip_layout.addWidget(QLabel("IP Address:"))
        self.ip_address_input = QLineEdit()
        self.ip_address_input.setPlaceholderText("Your IP (auto-detect)")
        ip = self._get_local_ip()         # auto-detect
        if ip: self.ip_address_input.setText(ip)
        self.ip_address_input.setEnabled(False)
        ip_layout.addWidget(self.ip_address_input)
        layout.addLayout(ip_layout)
        self.port = 9999
        self.start_network_button = QPushButton("Start Hosting")
        self.start_network_button.clicked.connect(self._start_or_connect_network_game)
        layout.addWidget(self.start_network_button, alignment=Qt.AlignCenter)
        self.network_controls_group.setLayout(layout)

    def _get_local_ip(self):
        '''
        Return the machine's LAN IP (not 127.0.0.1) by opening a UDP socket to a non-routable address (no packets sent).
        
        - By “connecting” a UDP socket to a non-routable address, 
        you force the OS to pick which local interface (and IP) 
        it would use to send to that destination without actually sending any packets.
        - If that comes back as 127.0.0.1, it falls back to the hostname, 
        which usually gives you your LAN IP instead of loopback.
        - Then it closes the socket and returns whatever IP it found (or None on error).
        '''
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
            if ip == '127.0.0.1':
                ip = socket.gethostbyname(socket.gethostname())
            return ip
        except: return None
        finally:
            if s: s.close()

    def _update_ip_input_state(self):
        # toggle ip field for client vs host
        is_client = self.client_radio.isChecked()
        self.ip_address_input.setEnabled(is_client)
        self.ip_address_input.setPlaceholderText(
            "Enter Host IP" if is_client else "Your IP (auto)"
        )
        # swap the button label
        if is_client:
            self.start_network_button.setText("Connect to Host")
        else:
            self.start_network_button.setText("Start Hosting")

        
        # reset ip text
        if not is_client:
            ip = self._get_local_ip()
            self.ip_address_input.setText(ip or "")
        else:
            self.ip_address_input.setText("")

    def _create_bottom_controls(self):
        # status label + rematch/reset buttons
        self.controls_bottom_widget = QWidget()
        hl = QHBoxLayout(self.controls_bottom_widget)
        self.controls_bottom_widget.setStyleSheet("background: transparent;")
        self.message_label = QLabel("")
        f = QFont(); f.setPointSize(12); self.message_label.setFont(f)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.message_label.setWordWrap(True)
        self.reset_button = QPushButton("Reset"); self.reset_button.clicked.connect(self.reset_game)
        self.rematch_button = QPushButton("Rematch?"); self.rematch_button.clicked.connect(self._request_rematch)
        self.accept_rematch_button = QPushButton("Accept"); self.accept_rematch_button.clicked.connect(self._accept_rematch)
        self.decline_rematch_button = QPushButton("Decline"); self.decline_rematch_button.clicked.connect(self._decline_rematch)
        for w in (self.message_label, None, self.rematch_button,
                  self.accept_rematch_button, self.decline_rematch_button,
                  self.reset_button):
            if w: hl.addWidget(w)
            else: hl.addStretch(1)
        self.bottom_layout = hl

    def _update_rematch_buttons_visibility(self):
        # show/hide rematch or accept/decline
        net_over = self.game_mode in ("host","client") and self.game_logic.game_over
        req = net_over and not self.rematch_requested_by_me and not self.rematch_requested_by_opponent
        acc = net_over and self.rematch_requested_by_opponent
        self.rematch_button.setVisible(req); self.rematch_button.setEnabled(req)
        self.accept_rematch_button.setVisible(acc); self.decline_rematch_button.setVisible(acc)
        # disable reset if waiting on rematch
        ok = not (self.rematch_requested_by_me or self.rematch_requested_by_opponent)
        self.reset_button.setEnabled(ok)

    @Slot(str)
    def _update_message(self, text, is_error=False,
                         is_success=False, is_turn=False):
        # set message text + style
        style = "color: #eee;"
        if is_error:   style = "color: #ff8a8a; font-weight: bold;"
        elif is_success: style = "color: lime; font-weight: bold;"
        elif is_turn:    style = "color: #8acaff; font-weight: bold;"
        self.message_label.setStyleSheet(style)
        self.message_label.setText(text)

    def _update_network_ui_state(self, enabled):
        # enable/disable network controls
        self.network_controls_group.setEnabled(enabled)

    def _enable_network_setup(self):
        # switch to network mode
        self.reset_game()
        self._update_network_ui_state(True)
        self._update_message("setup network game.")

    @Slot()
    def _start_or_connect_network_game(self):
        # start host or client thread
        if self.network_thread and self.network_thread.isRunning():
            self._update_message("network active.", is_error=True)
            return
        self._stop_network_worker()
        ip = self.ip_address_input.text().strip()
        if self.host_radio.isChecked():
            self.game_mode='host'
            host_ip = ip or self._get_local_ip()
            if not host_ip or host_ip=='127.0.0.1':
                self._update_message("Enter valid host ip", is_error=True)
                return
            self.ip_address_input.setText(host_ip)
            self._setup_and_start_worker()
            self.network_worker.start_hosting(host_ip, self.port)
        else:
            self.game_mode='client'
            if not ip:
                QMessageBox.warning(self, "Network Error", "Enter host ip")
                return
            self._setup_and_start_worker()
            self.network_worker.start_connecting(ip, self.port)
        # lock ui
        self._update_network_ui_state(False)
        self.board_widget.set_accept_clicks(False)
        self.who_started_last_round='X'

    def _setup_and_start_worker(self):
        # create thread + worker + connect signals
        self.network_thread = QThread(self)
        self.network_worker = NetworkWorker()
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
        self.network_thread.started.connect(lambda: print("network thread started"))
        self.network_thread.finished.connect(self._on_network_thread_finished)
        self.network_thread.finished.connect(self.network_worker.deleteLater)
        self.network_thread.start()

    @Slot(str)
    def _on_assign_symbol(self, symbol):
        # set player symbols + first turn
        self.my_symbol = symbol
        self.opponent_symbol = 'O' if symbol=='X' else 'X'
        self._update_message(f"network game started. you are '{self.my_symbol}'.")
        self.is_my_turn = (self.my_symbol==self.who_started_last_round)
        self.board_widget.set_accept_clicks(self.is_my_turn)
        if self.is_my_turn:
            self._update_message(f"Your ({self.my_symbol}) turn.", is_turn=True)
        else:
            txt = f"Waiting for opponent ('{self.opponent_symbol}') move..."
            self._update_message(txt)
        self._update_rematch_buttons_visibility()

    @Slot()
    def _on_network_connected(self):
        pass  # connected signal received

    @Slot(str)
    def _on_network_disconnected(self, reason):
        # handle abrupt disconnect
        if self.game_mode!='local':
            self._update_message(f"Disconnected: {reason}", is_error=True)
            QMessageBox.information(self, "Disconnected", reason)
            self.reset_game()

    @Slot(str)
    def _on_network_error(self, err):
        # show error + revert to local
        if self.game_mode!='local':
            self._update_message(f"Network error: {err}", is_error=True)
            QMessageBox.critical(self, "Network Error", err)
            self._stop_network_worker()
            self._update_network_ui_state(True)
            self.game_mode='local'; self.is_my_turn=True
            self.board_widget.set_accept_clicks(True)
            self._update_rematch_buttons_visibility()

    @Slot(str)
    def _on_status_update(self, stat):
        # status from network worker
        self._update_message(stat)

    @Slot()
    def _on_network_thread_finished(self):
        # cleanup after thread ends
        print("network thread finished")
        self.network_thread = None; self.network_worker = None
        if self.game_mode!='local' and not self.game_logic.game_over:
            self._update_message("connection ended unexpectedly", is_error=True)
            self._update_rematch_buttons_visibility()

    def _handle_game_over(self, msg, ok):
        # end game UI updates
        self._update_message(msg, is_success=ok, is_error=not ok)
        self.board_widget.set_accept_clicks(False)
        self.is_my_turn=False
        self._update_rematch_buttons_visibility()

    @Slot(int, int)
    def _on_cell_clicked(self, r, c):
        # ignore clicks after game over
        if self.game_logic.game_over:
            return

        # ——— LOCAL MODE ———
        if self.game_mode == 'local':
            p = 'X' if self.game_logic.move_count % 2 == 0 else 'O'
            res = self.game_logic.make_move(r, c, p)
            if res != "invalid":
                self.board_widget.update()
                if res == "win":
                    self._handle_game_over(f"player {p} wins!", True)
                elif res == "draw":
                    self._handle_game_over("it's a draw!", True)
                else:
                    nxt = 'X' if self.game_logic.move_count % 2 == 0 else 'O'
                    self._update_message(f"player {nxt}'s turn")
            return  # prevent falling into network logic

        # ——— NETWORK MODE ———
        # only allow click if it's your turn
        if not self.is_my_turn:
            self._update_message("not your turn", is_error=True)
            return

        if self.game_logic.is_cell_empty(r, c):
            res = self.game_logic.make_move(r, c, self.my_symbol)
            self.board_widget.update()
            if self.network_worker and self.network_worker._running:
                self.network_worker.send_move(r, c)
            if res == "win":
                self._handle_game_over(f"You ({self.my_symbol}) win!", True)
            elif res == "draw":
                self._handle_game_over("it's a draw!", True)
            else:
                self.is_my_turn = False
                self.board_widget.set_accept_clicks(False)
                self._update_message(
                    f"waiting for opponent ('{self.opponent_symbol}') move..."
                )
        else:
            self._update_message("cell taken", is_error=True)

    @Slot(int, int)
    def _on_move_received(self, r, c):
        # when opponent moves
        if self.game_logic.game_over or self.game_mode=='local': return
        res = self.game_logic.make_move(r, c, self.opponent_symbol)
        self.board_widget.update()
        if res=="win": self._handle_game_over(f"Opponent ({self.opponent_symbol}) wins!", False)
        elif res=="draw": self._handle_game_over("It's a draw!", True)
        elif res=="continue":
            self.is_my_turn=True
            self.board_widget.set_accept_clicks(True)
            self._update_message(f"Your ({self.my_symbol}) turn!", is_turn=True)

    @Slot()
    def _request_rematch(self):
        # ask opponent for rematch
        if self.network_worker and self.network_worker._running:
            self.network_worker.send_rematch_request()
            self.rematch_requested_by_me=True
            self._update_message("rematch requested...")
            self._update_rematch_buttons_visibility()

    @Slot()
    def _accept_rematch(self): self.network_worker.send_rematch_accept(); self._start_new_round()
    @Slot()
    def _decline_rematch(self):
        # decline and stay in game over
        self.network_worker.send_rematch_decline()
        self.rematch_requested_by_opponent=False
        self._update_message("Rematch declined.")
        self._update_rematch_buttons_visibility()

    @Slot()
    def _handle_rematch_request(self):
        # got rematch ask
        if self.game_logic.game_over:
            self.rematch_requested_by_opponent=True
            self._update_message("Opponent wants rematch")
            self._update_rematch_buttons_visibility()

    @Slot()
    def _handle_rematch_accepted(self):
        # opponent agreed
        if self.rematch_requested_by_me:
            self._update_message("Rematch accepted")
            self._start_new_round()

    @Slot()
    def _handle_rematch_declined(self):
        # opponent declined
        if self.rematch_requested_by_me:
            self.rematch_requested_by_me=False
            self._update_message("Rematch declined")
            self._update_rematch_buttons_visibility()

    def _start_new_round(self):
        # clear board + swap starter
        self.game_logic.reset_game()
        self.rematch_requested_by_me=False; self.rematch_requested_by_opponent=False
        self.who_started_last_round = 'O' if self.who_started_last_round=='X' else 'X'
        self.is_my_turn = (self.my_symbol==self.who_started_last_round)
        self.board_widget.set_accept_clicks(self.is_my_turn)
        self.board_widget.update()
        self._update_rematch_buttons_visibility()
        if self.is_my_turn:
            self._update_message(f"New round your ({self.my_symbol}) turn", is_turn=True)
        else:
            self._update_message(f"New round waiting for opponent", is_turn=False)

    def _stop_network_worker(self):
        # stop thread + sockets
        self._explicit_stop=True
        if self.network_worker:
            try: self.network_worker.stop()
            except: pass
        if self.network_thread and self.network_thread.isRunning():
            self.network_thread.quit()
            if not self.network_thread.wait(1000): self.network_thread.terminate()
        self.network_thread=None; self.network_worker=None
        self._explicit_stop=False

    @Slot()
    def reset_game(self):
        # full reset to local
        self._stop_network_worker()
        self.game_logic.reset_game()
        self.game_mode='local'; self.my_symbol='X'; self.opponent_symbol='O'; self.is_my_turn=True
        self.rematch_requested_by_me=False; self.rematch_requested_by_opponent=False
        self.who_started_last_round='X'
        self._update_message("new local game, player x turn")
        self.message_label.setStyleSheet("")
        self.board_widget.set_accept_clicks(True); self.board_widget.update()
        self._update_network_ui_state(True)
        self._update_rematch_buttons_visibility()

    def closeEvent(self, event):
        # ensure cleanup on close
        self._stop_network_worker()
        event.accept()
