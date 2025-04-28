import threading, socket
from PySide6.QtCore import QObject, Signal, Slot

NET_MSG_PREFIX = "NET::"
REQ_REMATCH = NET_MSG_PREFIX + "REQ_REMATCH"
ACK_REMATCH = NET_MSG_PREFIX + "ACK_REMATCH"
DEC_REMATCH = NET_MSG_PREFIX + "DEC_REMATCH"

class NetworkWorker(QObject):
    """
    qt worker for network i/o and messaging
    """
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
        """
        init sockets and control flags
        """
        super().__init__()
        self.socket = None
        self.server_socket = None
        self.host_ip = ""       # ip to bind or connect
        self.port = 0
        self.is_hosting = False # host vs client mode
        self._running = False   # thread control flag
        self.connection_thread = None

    def _start_connection_thread(self, target_func, args_tuple):
        """
        spawn daemon thread for host/connect
        """
        # only one thread at a time
        if self.connection_thread and self.connection_thread.is_alive(): return
        self._running = True
        self.connection_thread = threading.Thread(
            target=target_func,
            args=args_tuple,
            daemon=True
        )
        self.connection_thread.start()

    @Slot(str, int)
    def start_hosting(self, host_ip, port):
        """
        begin listening as host
        """
        self.host_ip = host_ip; self.port = port; self.is_hosting = True
        self._start_connection_thread(self._host_thread_func, ())

    @Slot(str, int)
    def start_connecting(self, host_ip, port):
        """
        connect to a host
        """
        self.host_ip = host_ip; self.port = port; self.is_hosting = False
        self._start_connection_thread(self._connect_thread_func, ())

    def _host_thread_func(self):
        """
        host socket loop: accept one client then handle msgs
        """
        self.server_socket = None
        try:
            # setup listening socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host_ip, self.port))
            self.server_socket.listen(1)
            self.status_update.emit(f"listening on {self.host_ip}:{self.port}. waiting...")
            self.server_socket.settimeout(1.0)
            client_socket = None

            # wait for connection or stop
            while self._running and client_socket is None:
                try:
                    client_socket, addr = self.server_socket.accept()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._running: self.error_occurred.emit(f"accept error: {e}")
                    self._running = False
                    break

            if self.server_socket:
                self.server_socket.settimeout(None)

            # stopped before connect
            if not self._running:
                if client_socket: client_socket.close()
                return

            # client connected
            self.socket = client_socket
            self.status_update.emit(f"opponent connected from {addr[0]}:{addr[1]}")
            self.assign_player_symbol.emit('X'); self.connected.emit()
            self._handle_connection()

        except (socket.error, ConnectionAbortedError) as e:
            if self._running: self.error_occurred.emit(f"hosting error: {e}")
        except Exception as e:
            if self._running: self.error_occurred.emit(f"unexpected hosting error: {e}")
        finally:
            serv = self.server_socket
            self.server_socket = None
            if serv:
                try: serv.close()
                except: pass  # ignore close errors

    def _connect_thread_func(self):
        """
        client socket setup and handshake
        """
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.status_update.emit(f"connecting to {self.host_ip}:{self.port}...")
            client_socket.settimeout(10.0)
            client_socket.connect((self.host_ip, self.port))
            client_socket.settimeout(None)

            if not self._running:
                client_socket.close()
                raise ConnectionAbortedError("connection stopped")

            self.socket = client_socket
            self.status_update.emit("connected to host.")
            self.assign_player_symbol.emit('O'); self.connected.emit()
            self._handle_connection()

        except socket.timeout:
            if self._running:
                self.error_occurred.emit(f"connection timed out to {self.host_ip}:{self.port}.")
        except socket.gaierror:
            if self._running:
                self.error_occurred.emit(f"address error connecting to {self.host_ip}")
        except (socket.error, ConnectionAbortedError) as e:
            if self._running:
                self.error_occurred.emit(f"connection error: {e}")
        except Exception as e:
            if self._running:
                self.error_occurred.emit(f"unexpected connection error: {e}")
        finally:
            # cleanup on failed connect
            if not self._running and self.socket:
                try: self.socket.close()
                except: pass
                self.socket = None

    def _handle_connection(self):
        """
        main loop: recv msgs, emit signals
        """
        while self._running and self.socket:
            try:
                data = self.socket.recv(1024)
                if not data:
                    if self._running: self.disconnected.emit("opponent disconnected")
                    self._running = False; break

                msg = data.decode('utf-8')
                # rematch commands
                if msg.startswith(NET_MSG_PREFIX):
                    if msg == REQ_REMATCH: self.rematch_request_received.emit()
                    elif msg == ACK_REMATCH: self.rematch_accepted.emit()
                    elif msg == DEC_REMATCH: self.rematch_declined.emit()
                    else: print(f"unknown net msg: {msg}")
                else:
                    parts = msg.split(',')
                    if len(parts)==2:
                        r,c = int(parts[0]), int(parts[1])
                        if 0<=r<=2 and 0<=c<=2: self.move_received.emit(r,c)
                        else: print(f"oob move: {msg}")
                    else:
                        print(f"malformed move data: {msg}")

            except ConnectionResetError:
                if self._running: self.disconnected.emit("connection lost")
                self._running=False; break
            except socket.error as e:
                if self._running: self.disconnected.emit(f"socket error: {e}")
                self._running=False; break
            except ValueError:
                print(f"non-int move data: {msg}")
            except Exception as e:
                if self._running: self.disconnected.emit(f"recv error: {e}")
                self._running=False; break

        # tear down socket
        s = self.socket
        self.socket = None
        if s:
            try: s.close()
            except: pass

    def _send_message(self, message):
        """
        send raw msg over socket, handle errors
        """
        if self.socket and self._running:
            try:
                self.socket.sendall(message.encode('utf-8'))
                return True
            except socket.error as e:
                if self._running: self.disconnected.emit(f"send error: {e}")
                self._running=False
            except Exception as e:
                if self._running: self.disconnected.emit(f"unexpected send error: {e}")
                self._running=False

            # cleanup on send fail
            if self.socket:
                try: self.socket.close()
                except: pass
                self.socket=None
        return False

    @Slot(int, int)
    def send_move(self, row, col):
        # fire off a move
        self._send_message(f"{row},{col}")

    @Slot()
    def send_rematch_request(self): self._send_message(REQ_REMATCH)  # ask for another round

    @Slot()
    def send_rematch_accept(self): self._send_message(ACK_REMATCH)   # accepted rematch

    @Slot()
    def send_rematch_decline(self): self._send_message(DEC_REMATCH)  # declined rematch

    @Slot()
    def stop(self):
        """
        stop threads, close sockets
        """
        if not self._running: return
        self._explicit_stop = True
        self._running = False
        # close client socket
        if self.socket:
            try: self.socket.shutdown(socket.SHUT_RDWR)
            except: pass
            try: self.socket.close()
            except: pass
            self.socket=None
        # close server socket
        if self.server_socket:
            try: self.server_socket.close()
            except: pass
            self.server_socket=None
        self._explicit_stop=False
