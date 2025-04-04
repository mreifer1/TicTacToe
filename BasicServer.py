import socket
import sys
import threading

serverPort = 8888
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def respond(connectionSocket, address):
    request = connectionSocket.recv(1024).decode()

    ###### Fill in Start ######
    lines = request.split("\r\n")
    request_line = lines[0]
    method = request_line.split()[0]

    for line in lines:
        print(line)

    response = 'HTTP/1.1 200 OK\r\n'
    print(response) 

    connectionSocket.send(response.encode())
    connectionSocket.close()
    ###### Fill in End ######

    return

# start the web server
try:
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # would have to change ip for different location (this is towsons local ipv4)
    serverSocket.bind(('10.128.192.21', serverPort))
    print("The server is ready to receive on port {port}.\n".format(port=serverPort))
except Exception as e:
    print("An error occurred on port {port}\n".format(port=serverPort))
    serverSocket.close()
    sys.exit(1)

serverSocket.listen(1)

# handle requests
while True:
    (connectionSocket, address) = serverSocket.accept()
    print("Received connection from {addr}\n".format(addr=address))
    threading.Thread(target=respond, args=(connectionSocket, address)).start()
