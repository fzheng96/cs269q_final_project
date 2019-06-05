#!/usr/bin/env python3
import json
import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
QVM_PORT = 60000        # The port used by the server
BOB_PORT = 60002

SELF_PORT = 60003
result = None
bell_basis = None

def parse_data(data, s):
    global result
    global bell_basis
    if data['name'] == 'alice':
        if data['command'] == 'tell_charlie_to_measure':
            message = {'name': 'charlie'}
            message['command'] = 'measure_in_x'
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, QVM_PORT))
            str_message = json.dumps(message)
            s.sendall(str_message.encode(encoding='UTF-8'))

            # getting back result
            data = s.recv(1024)
            str_data = data.decode("utf-8")
            result = json.loads(str_data)
            s.close()
        elif data['command'] == 'tell_charlie_to_reconstruct':
            bell_basis = data['bell_basis']
        elif data['command'] == 'tell_charlie_to_send_to_bob':
            message = {'name': 'charlie'}
            message['command'] = 'tell_bob_to_reconstruct'
            message['x_measurement'] = result
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, BOB_PORT))
            str_message = json.dumps(message)
            s.sendall(str_message.encode(encoding='UTF-8'))
            s.close()

    elif data['name'] == 'bob':
        if data['command'] == 'tell_charlie_to_reconstruct':
            x_measurement = data['x_measurement']
            message = {'name': 'charlie'}
            message['command'] = 'reconstruct_state'
            message['bell_basis'] = bell_basis
            message['x_measurement'] = x_measurement
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, QVM_PORT))
            str_message = json.dumps(message)
            s.sendall(str_message.encode(encoding='UTF-8'))

            # wave function result
            data = s.recv(1024)
            str_data = data.decode('utf-8')
            result = json.loads(str_data)
            s.close()
            print("Wavefunction: {}".format(result))


while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, SELF_PORT))
    s.listen()
    conn, addr = s.accept()
    data = conn.recv(1024)
    conn.close()
    s.close()
    str_data = data.decode("utf-8")
    print(json.loads(str_data))
    parse_data(json.loads(str_data), s)