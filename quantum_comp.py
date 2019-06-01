#!/usr/bin/env python3
import json
import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 60000        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    while True:
        s.listen()
        conn, addr = s.accept()
        with conn:
            data = conn.recv(1024)
            str_data = data.decode("utf-8")
            if not data:
                break
            print(json.loads(str_data))
            conn.sendall(data)
            conn.close()
