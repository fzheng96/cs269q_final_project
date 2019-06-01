#!/usr/bin/env python3
import json
import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
QVM_PORT = 60000        # The port used by the server
BOB_PORT = 60002
CHARLIE_PORT = 60003

SELF_PORT = 60001

# Initialize sharing protocol
message = {'name': 'alice'}
alpha = input("What's the alpha you want to send? ")
beta = input("What's the beta you want to send? ")
message['command'] = "initialize_sharing_protocol"
message['qubit'] = (alpha, beta)
str_message = json.dumps(message)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, QVM_PORT))
s.sendall(str_message.encode(encoding='UTF-8'))
s.close()

# Measure in Bell Basis
message = {'name': 'alice'}
command = input("Next command: ")
message['command'] = command
if command != "measure_bell_basis":
    raise Exception('The command needs to be measure_bell_basis')
str_message = json.dumps(message)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, QVM_PORT))
s.sendall(str_message.encode(encoding='UTF-8'))
data = s.recv(1024)
str_data = data.decode("utf-8")
bell_basis = json.loads(str_data)
print("Bell basis: {}".format(bell_basis))
s.close()

# Choose Bob or Charlie to send qubit to
message = {'name': 'alice'}
command = input("Next command: ")
message['command'] = str(command)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if command == "tell_bob_to_measure":
    s.connect((HOST, BOB_PORT))
elif command == 'tell_charlie_to_measure':
    s.connect((HOST, CHARLIE_PORT))
else:
    raise Exception("You must choose Bob or Charlie to measure")
str_message = json.dumps(message)
s.sendall(str_message.encode(encoding='UTF-8'))
s.close()

# Send bell basis to other person
message = {'name': 'alice'}
command = input("Next command: ")
message['command'] = command
message['bell_basis'] = bell_basis
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if command == "tell_bob_to_reconstruct":
    s.connect((HOST, BOB_PORT))
elif command == 'tell_charlie_to_reconstruct':
    s.connect((HOST, CHARLIE_PORT))
else:
    raise Exception("You must choose Bob or Charlie to measure")
str_message = json.dumps(message)
s.sendall(str_message.encode(encoding='UTF-8'))
s.close()

# Tell first person to send their result back to second person
message = {'name': 'alice'}
command = input("Next command: ")
message['command'] = command
message['bell_basis'] = bell_basis
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if command == "tell_bob_to_send_to_charlie":
    s.connect((HOST, BOB_PORT))
elif command == 'tell_charlie_to_send_to_bob':
    s.connect((HOST, CHARLIE_PORT))
else:
    raise Exception("You must choose Bob or Charlie to measure")
str_message = json.dumps(message)
s.sendall(str_message.encode(encoding='UTF-8'))
s.close()