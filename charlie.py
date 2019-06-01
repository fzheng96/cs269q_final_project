#!/usr/bin/env python3
import json
import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 60000        # The port used by the server

SELF_PORT = 60003

while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    message = {'name': ''}
    name = input("What's the next command? ")
    message['command'] = name
    str_message = json.dumps(message)
    s.sendall(str_message.encode(encoding='UTF-8'))
    data = s.recv(1024)
    print("Received", repr(data))
    s.close()