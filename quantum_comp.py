#!/usr/bin/env python3
import json
import socket
import ast

from pyquil import Program
from pyquil.quil import DefGate
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator, QVMConnection

from grove.alpha.arbitrary_state.arbitrary_state import create_arbitrary_state

import numpy as np

NUM_TRIALS = 1

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 60000        # Port to listen on (non-privileged ports are > 1023)

qvm = QVMConnection(random_seed=1337)

p = None
ro = None

def ghz_state(qubits=[1,2,3]):
    """
    Create a GHZ state on the given list of qubits by applying a
    Hadamard gate to the first qubit followed by a chain of CNOTs
    """
    program = Program()
    program += H(qubits[0])
    for q1, q2 in zip(qubits, qubits[1:]):
        program += CNOT(q1, q2)
    return program

def reconstruct(p, bob_or_charlie, bell, x_measurement):
        """
        Reconstructs the wave function (alpha betas) by applying the
        appropriate operators determined from two qubits from Alice
        and one qubit from Bob

        @params
        p: secret sharing program
        bob_or_charlie: The person who Alice told to make the measurement
        result: Alice's result from measuring in the Bell basis
        """
        reconstruct_idx = 2
        if bob_or_charlie == 2:
            reconstruct_idx = 3
        bell = ast.literal_eval(bell)
        if bell == [0, 0] and x_measurement == 1:
            p += I(reconstruct_idx)
        elif bell == [0, 0] and x_measurement == 0:
            p += Z(reconstruct_idx)
        elif bell == [0, 1] and x_measurement == 1:
            p += Z(reconstruct_idx)
        elif bell == [0, 1] and x_measurement == 0:
            p += I(reconstruct_idx)
        elif bell == [1, 0] and x_measurement == 1:
            p += X(reconstruct_idx)
        elif bell == [1, 0] and x_measurement == 0:
            p += Z(reconstruct_idx)
            p += X(reconstruct_idx)
        elif bell == [1, 1] and x_measurement == 1:
            p += Z(reconstruct_idx)
            p += X(reconstruct_idx)
        elif bell == [1, 1] and x_measurement == 0:
            p += X(reconstruct_idx)
        else:
            raise Exception('Bell state or bob_or_charlie\'s measurement' +
                'was wrong')

        wavefunction_simulator = WavefunctionSimulator()
        wavefunction = wavefunction_simulator.wavefunction(p)

        return wavefunction

def parse_data(data, s, conn):
    """
    @params data: dictionary of message
    """
    global p
    global ro
    if data['name'] == 'alice':
        if data['command'] == 'initialize_sharing_protocol':
            alpha, beta = data['qubit']
            p = create_arbitrary_state([float(alpha), float(beta)])
            p += ghz_state()
            ro = p.declare('ro', 'BIT', 3)
        elif data['command'] == 'measure_bell_basis':
            p += CNOT(1, 0)
            p += H(1)
            p += MEASURE(0, ro[0])
            p += MEASURE(1, ro[1])
            p_copy = p.copy()
            result = str(qvm.run(p_copy, trials=NUM_TRIALS)[0])
            json_msg = json.dumps(result)
            print("Bell basis: {}".format(result))
            conn.sendall(json_msg.encode(encoding='UTF-8'))
    elif data['name'] == 'bob':
        if data['command'] == 'measure_in_x':
            p += H(2)
            p += MEASURE(2, ro[2])
            p_copy = p.copy()
            result = qvm.run(p_copy, trials=NUM_TRIALS)[0]
            print("Result of measuring in x: {}".format(result))
            json_msg = json.dumps(result[2])
            conn.sendall(json_msg.encode(encoding='UTF-8'))
        elif data['command'] == 'reconstruct_state':
            bell_basis = data['bell_basis']
            x_measurement = data['x_measurement']

            wavefunction = reconstruct(p, 2, bell_basis, x_measurement)

            curr_reconstructed = []
            for amplitude in wavefunction.amplitudes:
                if not np.allclose([amplitude], [0]):
                    curr_reconstructed.append(amplitude)
            curr_reconstructed = str(np.array(curr_reconstructed))
            json_msg = json.dumps(curr_reconstructed)
            conn.sendall(json_msg.encode(encoding='UTF-8'))


    elif data['name'] == 'charlie':
        if data['command'] == 'measure_in_x':
            p += H(3)
            p += MEASURE(3, ro[2])
            p_copy = p.copy()
            result = qvm.run(p_copy, trials=NUM_TRIALS)[0]
            print("Result of measuring in x: {}".format(result))
            json_msg = json.dumps(result[2])
            conn.sendall(json_msg.encode(encoding='UTF-8'))
        elif data['command'] == 'reconstruct_state':
            bell_basis = data['bell_basis']
            x_measurement = data['x_measurement']
            wavefunction = reconstruct(p, 3, bell_basis, x_measurement)

            curr_reconstructed = []
            for amplitude in wavefunction.amplitudes:
                if not np.allclose([amplitude], [0]):
                    curr_reconstructed.append(amplitude)
            curr_reconstructed = str(np.array(curr_reconstructed))
            json_msg = json.dumps(curr_reconstructed)
            conn.sendall(json_msg.encode(encoding='UTF-8'))

    else:
        raise Exception("Data name parsing is wrong")

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
            parse_data(json.loads(str_data), s, conn)
            conn.close()
