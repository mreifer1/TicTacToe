import socket
import threading
import sys
import time

class TicTacToe:
    """
    Manages the state and logic for a network Tic-Tac-Toe game.
    Can act as either the host or the client.
    """

    def __init__(self):
        """Initializes the game board and state variables."""
        self.board = [[" ", " ", " "], [" ", " ", " "], [" ", " ", " "]]
        self.turn = "X"         # X always starts
        self.you = "X"
        self.opponent = "O"
        self.winner = None
        self.game_over = False
        self.counter = 0
        self.connection = None

    def host_game(self, host, port):
        """
        Sets up the game server, waits for a client connection,
        and starts the game handling thread.
        """
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # allow reusing the address (helpful for quick restarts)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((host, port))
            server.listen(1)
            print(f"[*] Listening on {host}:{port}")
            print("[*] Waiting for opponent to connect...")

            client, addr = server.accept()
            self.connection = client
            print(f"[*] Opponent connected from {addr[0]}:{addr[1]}")

            self.you = "X"
            self.opponent = "O"

            print("Game started! You are 'X'.")
            self.print_board()

            # start thread to handle game communication
            # daemon=True allows exiting if main thread finishes
            threading.Thread(target=self.handle_connection, args=(client,), daemon=True).start()

            # close the server listening socket
            # the accepted 'client' socket handles communication
            server.close()
            print("[*] Server listening socket closed.")

        except socket.error as e:
            print(f"[!] Socket Error hosting game: {e}")
            print("[!] Make sure the IP address is correct and the port is not already in use.")
            sys.exit(1)
        except Exception as e:
            print(f"[!] An unexpected error occurred during hosting setup: {e}")
            sys.exit(1)

    def connect_to_game(self, host, port):
        """
        Connects to a host server and starts the game handling thread.
        """
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"[*] Connecting to {host}:{port}...")
            client.connect((host, port))
            self.connection = client
            print(f"[*] Successfully connected to the host.")

            self.you = 'O'
            self.opponent = 'X'

            print("Game started! You are 'O'.")
            self.print_board()

            # start thread to handle game communication
            threading.Thread(target=self.handle_connection, args=(client,), daemon=True).start()

        except socket.gaierror:
             print(f"[!] Address-related error connecting to server ({host}:{port}). Check the IP/hostname.")
             sys.exit(1)
        except socket.error as e:
            print(f"[!] Socket Error connecting to game: {e}")
            print("[!] Make sure the host IP and port are correct and the host is running.")
            sys.exit(1)
        except Exception as e:
            print(f"[!] An unexpected error occurred during connection: {e}")
            sys.exit(1)

    def handle_connection(self, client_socket):
        """
        Handles sending and receiving moves over the provided socket connection.
        This function runs in a separate thread.
        """
        while not self.game_over:
            if self.turn == self.you:
                # your turn
                move = input(f"Your turn ({self.you}). Enter move (row,col) from 0-2: ").strip()
                if ',' in move:
                    try:
                        row_col = move.split(',')
                        row, col = int(row_col[0]), int(row_col[1])

                        if 0 <= row <= 2 and 0 <= col <= 2:
                            if self.check_valid_move((row, col)):
                                self.apply_move((row, col), self.you)
                                client_socket.send(move.encode('utf-8'))
                                self.turn = self.opponent
                                if self.game_over: break # check immediately after move
                            else:
                                print("!! Cell already taken. Try again.")
                        else:
                           print("!! Invalid row/column number. Must be between 0 and 2.")
                    except ValueError:
                        print("!! Invalid input. Please enter numbers for row and column (e.g., 1,1).")
                    except Exception as e:
                         print(f"!! Error processing move: {e}")
                else:
                    print("!! Invalid input format. Use row,col (e.g., 0,0 or 1,2).")
            else:
                # opponent's turn
                print(f"Waiting for opponent ({self.opponent})'s move...")
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        print("\n[!] Opponent disconnected.")
                        self.game_over = True
                        break

                    move_str = data.decode('utf-8')
                    print(f"Opponent ({self.opponent}) played: {move_str}")

                    try:
                        row_col = move_str.split(',')
                        row, col = int(row_col[0]), int(row_col[1])
                        # Sanity check opponent move validity
                        if self.check_valid_move((row, col)):
                             self.apply_move((row, col), self.opponent)
                             self.turn = self.you
                             if self.game_over: break # check immediately after move
                        else:
                            print("[!] Received invalid move from opponent (cell taken?). Ending game.")
                            self.game_over = True
                            break
                    except (ValueError, IndexError):
                        print("[!] Received malformed move data from opponent. Ending game.")
                        self.game_over = True
                        break

                except ConnectionResetError:
                     print("\n[!] Connection lost with opponent.")
                     self.game_over = True
                     break
                except socket.error as e:
                    print(f"\n[!] Socket error during receive: {e}")
                    self.game_over = True
                    break
                except Exception as e:
                    print(f"\n[!] An unexpected error occurred while receiving data: {e}")
                    self.game_over = True
                    break

        # the game over sequence
        print("\n--- Game Over ---")
        if self.winner:
            if self.winner == self.you: print("You won!!!")
            else: print("You lost!!! loser 🫵")
        elif self.counter == 9:
            print("It's a Tie!")
        else:
            print("Game ended.") # due to disconnection

        if self.connection:
            print("[*] Closing connection...")
            self.connection.close()
            self.connection = None
            print("[*] Connection closed.")

        print("Press Enter to exit.") # signal main thread or user


    def apply_move(self, move_coords, player):
        """
        Applies a move to the board, increments counter, prints board,
        and checks for win/tie conditions.
        Assumes move_coords is a tuple of integers (row, col).
        """
        if self.game_over: return

        row, col = move_coords
        if 0 <= row <= 2 and 0 <= col <= 2 and self.board[row][col] == " ":
            self.board[row][col] = player
            self.counter += 1
            self.print_board()

            if self.check_if_won():
                self.game_over = True
            elif self.counter == 9:
                self.game_over = True
        else:
            print(f"[!] Internal Error: Attempted invalid move ({row},{col}) by {player}.")


    def check_valid_move(self, move_coords):
        """
        Checks if the cell specified by move_coords (row, col tuple) is empty.
        Returns True if valid and empty, False otherwise.
        """
        try:
            row, col = move_coords
            if 0 <= row <= 2 and 0 <= col <= 2:
                return self.board[row][col] == " "
            else: return False # Out of bounds
        except Exception:
            return False # Invalid format


    def check_if_won(self):
        """
        Checks all rows, columns, and diagonals for a winning condition.
        Sets self.winner and returns True if a win is found, otherwise returns False.
        """
        # Check rows
        for r in range(3):
            if self.board[r][0] == self.board[r][1] == self.board[r][2] != " ":
                self.winner = self.board[r][0]; return True
        # Check columns
        for c in range(3):
            if self.board[0][c] == self.board[1][c] == self.board[2][c] != " ":
                self.winner = self.board[0][c]; return True
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != " ":
            self.winner = self.board[0][0]; return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != " ":
            self.winner = self.board[0][2]; return True

        return False

    def print_board(self):
        """Prints the current state of the Tic-Tac-Toe board to the console."""
        print("\n-------------")
        for i, row in enumerate(self.board):
            # Display cell content or column number if empty
            print(f"{i}  {' | '.join(cell if cell != ' ' else str(j) for j, cell in enumerate(row))}")
            if i < 2: print("  -----------")
        print("   0   1   2") # column indices
        print("-------------")


if __name__ == "__main__":
    print("--- Welcome to Network Tic-Tac-Toe ---")
    game = TicTacToe()
    DEFAULT_PORT = 9999

    # choose your role
    while True:
        choice = input("Do you want to (H)ost a game or (C)onnect to a game? [H/C]: ").strip().upper()
        if choice in ['H', 'C']: break
        else: print("Invalid choice. Please enter 'H' or 'C'.")

    # getting network details
    if choice == 'H':
        host_ip = ""
        try: # attemptting to auto-detect local IP
            s_temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s_temp.settimeout(0.1)
            s_temp.connect(('8.8.8.8', 80)) # connect to external server (doesn't send any data)
            detected_ip = s_temp.getsockname()[0]
            s_temp.close()
            print(f"Detected local IP: {detected_ip}")
            use_detected = input(f"Use this IP ({detected_ip})? (Y/n): ").strip().upper()
            host_ip = detected_ip if use_detected != 'N' else input("Enter the specific IP address you want to host on: ").strip()
        except Exception:
             print("Could not automatically determine local IP.")
             host_ip = input("Enter the IP address you want to host on (e.g., 192.168.1.5): ").strip()

        if not host_ip: print("Host IP cannot be empty. Exiting."); sys.exit(1)

        try: # getting the port
            port_str = input(f"Enter the port to host on (default {DEFAULT_PORT}): ").strip()
            port = int(port_str) if port_str else DEFAULT_PORT
            if not (1024 < port < 65535):
                 print(f"Warning: Port {port} outside typical user range (1024-65535). Using default {DEFAULT_PORT}.")
                 port = DEFAULT_PORT
        except ValueError:
            print(f"Invalid port number. Using default {DEFAULT_PORT}.")
            port = DEFAULT_PORT

        game.host_game(host_ip, port)

    elif choice == 'C':
        host_ip = input("Enter the host's IP address: ").strip()
        if not host_ip: print("Host IP cannot be empty. Exiting."); sys.exit(1)

        try: # getting the port
            port_str = input(f"Enter the host's port (default {DEFAULT_PORT}): ").strip()
            port = int(port_str) if port_str else DEFAULT_PORT
            if not (1024 < port < 65535):
                 print(f"Warning: Port {port} outside typical user range (1024-65535). Using default {DEFAULT_PORT}.")
                 port = DEFAULT_PORT
        except ValueError:
            print(f"Invalid port number. Using default {DEFAULT_PORT}.")
            port = DEFAULT_PORT

        game.connect_to_game(host_ip, port)

    # keep main thread alive while game thread runs
    while not game.game_over:
        try:
            time.sleep(1) # to prevent busy-waiting
        except KeyboardInterrupt:
            print("\n[!] Game interrupted by user (Ctrl+C).")
            game.game_over = True # signal handler thread
            if game.connection: game.connection.close() # graceful close
            break

    # Wait for user before final exit
    input("Game has finished. Press Enter to close the program.")
    print("Exiting.")
