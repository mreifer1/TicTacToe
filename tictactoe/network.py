import threading, socket
from PySide6.QtCore import QObject, Signal, Slot

NET_MSG_PREFIX = "NET::"
REQ_REMATCH = NET_MSG_PREFIX + "REQ_REMATCH"
ACK_REMATCH = NET_MSG_PREFIX + "ACK_REMATCH"
DEC_REMATCH = NET_MSG_PREFIX + "DEC_REMATCH"


class NetworkWorker(QObject):
    connected = Signal()
    disconnected = Signal(str)
    move_received = Signal(int, int)
    status_update = Signal(str)
    error_occurred = Signal(str)
    assign_player_symbol = Signal(str)
    rematch_request_received = Signal()
    rematch_accepted = Signal()
    rematch_declined = Signal()

    def __init__(self):
        super().__init__()
        self.socket = None
        self.server_socket = None
        self.host_ip = ""
        self.port = 0
        self.is_hosting = False
        self._running = False
        self.connection_thread = None

    def _start_connection_thread(self, target_func, args_tuple):
        if self.connection_thread and self.connection_thread.is_alive(): return
        self._running = True
        self.connection_thread = threading.Thread(target=target_func, args=args_tuple, daemon=True)
        self.connection_thread.start()

    @Slot(str, int)
    def start_hosting(self, host_ip, port):
        self.host_ip = host_ip; self.port = port; self.is_hosting = True
        self._start_connection_thread(self._host_thread_func, ())

    @Slot(str, int)
    def start_connecting(self, host_ip, port):
        self.host_ip = host_ip; self.port = port; self.is_hosting = False
        self._start_connection_thread(self._connect_thread_func, ())

    def _host_thread_func(self):
        self.server_socket = None
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host_ip, self.port))
            self.server_socket.listen(1)
            self.status_update.emit(f"Listening on {self.host_ip}:{self.port}. Waiting...")
            self.server_socket.settimeout(1.0)
            client_socket = None
            while self._running and client_socket is None:
                try:
                    client_socket, addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                except Exception as e:
                     if self._running: self.error_occurred.emit(f"Accept Error: {e}")
                     self._running = False
                     break

            if self.server_socket:
                self.server_socket.settimeout(None)

            if not self._running:
                if client_socket: client_socket.close()
                if not hasattr(self, '_explicit_stop') or not self._explicit_stop:
                     print("Hosting stopped while waiting for connection.")
                return

            if client_socket:
                self.socket = client_socket
                self.status_update.emit(f"Opponent connected from {addr[0]}:{addr[1]}")
                self.assign_player_symbol.emit('X'); self.connected.emit()
                self._handle_connection()

        except (socket.error, ConnectionAbortedError) as e:
            if self._running: self.error_occurred.emit(f"Hosting Error: {e}")
        except Exception as e:
             if self._running: self.error_occurred.emit(f"Unexpected Hosting Error: {e}")
        finally:
            serv_sock = self.server_socket
            self.server_socket = None
            if serv_sock:
                try:
                    serv_sock.close()
                    print("Server socket closed in finally block.")
                except OSError: pass

    def _connect_thread_func(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.status_update.emit(f"Connecting to {self.host_ip}:{self.port}...")
            client_socket.settimeout(10.0)
            client_socket.connect((self.host_ip, self.port))
            client_socket.settimeout(None)

            if not self._running: client_socket.close(); raise ConnectionAbortedError("Connection stopped.")
            self.socket = client_socket
            self.status_update.emit("Connected to host.")
            self.assign_player_symbol.emit('O'); self.connected.emit()
            self._handle_connection()
        except socket.timeout:
             if self._running: self.error_occurred.emit(f"Connection timed out to {self.host_ip}:{self.port}.")
        except socket.gaierror:
             if self._running: self.error_occurred.emit(f"Address error connecting to {self.host_ip}. Check IP.")
        except (socket.error, ConnectionAbortedError) as e:
            if self._running: self.error_occurred.emit(f"Connection Error: {e}. Is host running?")
        except Exception as e:
             if self._running: self.error_occurred.emit(f"Unexpected Connection Error: {e}")
        finally:
            if not self._running and self.socket:
                 try: self.socket.close()
                 except OSError: pass
                 self.socket = None


    def _handle_connection(self):
        while self._running and self.socket:
            try:
                data = self.socket.recv(1024)
                if not data:
                    if self._running: self.disconnected.emit("Opponent disconnected.")
                    self._running = False; break

                message = data.decode('utf-8')

                if message.startswith(NET_MSG_PREFIX):
                    if message == REQ_REMATCH:
                        self.rematch_request_received.emit()
                    elif message == ACK_REMATCH:
                        self.rematch_accepted.emit()
                    elif message == DEC_REMATCH:
                        self.rematch_declined.emit()
                    else:
                        print(f"Received unknown network message: {message}")
                else:
                    parts = message.split(',')
                    if len(parts) == 2:
                        row, col = int(parts[0]), int(parts[1])
                        if 0 <= row <= 2 and 0 <= col <= 2:
                            self.move_received.emit(row, col)
                        else:
                            print(f"Received out-of-bounds move: {message}")
                    else:
                        print(f"Received malformed move data: {message}")

            except ConnectionResetError:
                if self._running: self.disconnected.emit("Connection lost.")
                self._running = False; break
            except socket.error as e:
                if self._running: self.disconnected.emit(f"Socket Error: {e}")
                self._running = False; break
            except ValueError: print(f"Received non-integer move data: {message}")
            except Exception as e:
                if self._running: self.disconnected.emit(f"Receive Error: {e}")
                self._running = False; break
        sock = self.socket
        self.socket = None
        if sock:
            try: sock.close()
            except OSError: pass

    def _send_message(self, message):
        if self.socket and self._running:
            try:
                self.socket.sendall(message.encode('utf-8'))
                return True
            except socket.error as e:
                if self._running:
                    self.disconnected.emit(f"Send Error: {e}")
                self._running = False
                if self.socket:
                    try:
                        self.socket.close()
                    except OSError:
                        pass
                    self.socket = None
            except Exception as e:
                 if self._running:
                     self.disconnected.emit(f"Unexpected Send Error: {e}")
                 self._running = False
                 if self.socket:
                     try:
                         self.socket.close()
                     except OSError:
                         pass
                     self.socket = None
        return False

    @Slot(int, int)
    def send_move(self, row, col):
        move_str = f"{row},{col}"
        self._send_message(move_str)

    @Slot()
    def send_rematch_request(self):
        self._send_message(REQ_REMATCH)

    @Slot()
    def send_rematch_accept(self):
        self._send_message(ACK_REMATCH)

    @Slot()
    def send_rematch_decline(self):
        self._send_message(DEC_REMATCH)


    @Slot()
    def stop(self):
        if not self._running: return
        print("Stopping network worker...")
        self._explicit_stop = True
        self._running = False

        sock = self.socket
        self.socket = None
        if sock:
            try: sock.shutdown(socket.SHUT_RDWR)
            except OSError: pass
            try: sock.close(); print("Client socket closed by stop().")
            except OSError as e: print(f"Error closing client socket during stop: {e}")

        serv_sock = self.server_socket
        self.server_socket = None
        if serv_sock:
            try: serv_sock.close(); print("Server socket closed by stop().")
            except OSError as e: print(f"Error closing server socket during stop: {e}")
        self._explicit_stop = False
