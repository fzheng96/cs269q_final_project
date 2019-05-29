from pyquil import Program
from pyquil.quil import DefGate
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator, QVMConnection

from grove.alpha.arbitrary_state.arbitrary_state import create_arbitrary_state

import numpy as np

NUM_TRIALS = 1

class SecretSharing:

    def __init__(self, message):
        """
        This initializes the class for quantum secret sharing.

        Sets up an array of qubits to be shared.
        @params
        message: An array of tuples of alphas and betas which the caller
                 wants to be shared
                 ex. [(alpha_0, beta_0), (alpha_1, beta_1), ...]
        """
        self.programs = []
        self.alphas_betas = message
        self.qvm = QVMConnection(random_seed=1337)
        counter = 0
        for alpha, beta in message:
            if not np.allclose([(alpha ** 2) + (beta ** 2)], [1]):
                raise Exception('Invalid qubit setup: The alpha and betas ' +
                    'squared should equal 1.')
            p = create_arbitrary_state([alpha, beta])
            self.programs.append(p)
            counter += 1

    def share_secret(self):
        """
        Runs Hillery's quantum secret sharing splitting algorithm to make sure
        that Bob and Charlie have to work together to retrieve the original
        message that was to be sent
        """
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

        def reconstruct(p, bob_or_charlie, result):
            """
            Reconstructs the wave function (alpha betas) by applying the
            appropriate operators determined from two qubits from Alice
            and one qubit from Bob

            @params
            p: secret sharing program
            bob_or_charlie: The person who Alice told to make the measurement
            result: Alice's result from measuring in the Bell basis
            """
            ro = self.qvm.run(p, trials=NUM_TRIALS)[0]
            reconstruct_idx = 2
            if bob_or_charlie == 2:
                reconstruct_idx = 3

            bell = [ro[0], ro[1]]

            # This makes sure that the measurement that Bob or Charlie received
            # from Alice is the same as the measurement that she made by comparing
            # the result of running p with Alice's result
            if not np.allclose(bell, result):
                raise Exception("Measurement in Bell basis was tampered with")

            if bell == [0, 1] and ro[2] == 0:
                p += I(reconstruct_idx)
            elif bell == [0, 1] and ro[2] == 1:
                p += Z(reconstruct_idx)
            elif bell == [1, 1] and ro[2] == 0:
                p += Z(reconstruct_idx)
            elif bell == [1, 1] and ro[2] == 1:
                p += I(reconstruct_idx)
            elif bell == [0, 0] and ro[2] == 0:
                p += X(reconstruct_idx)
            elif bell == [0, 0] and ro[2] == 1:
                p += Z(reconstruct_idx)
                p += X(reconstruct_idx)
            elif bell == [1, 0] and ro[2] == 0:
                p += Z(reconstruct_idx)
                p += X(reconstruct_idx)
            elif bell == [1, 0] and ro[2] == 1:
                p += X(reconstruct_idx)
            else:
                raise Exception('Bell state or bob_or_charlie\'s measurement' +
                    'was wrong')

            wavefunction_simulator = WavefunctionSimulator()
            wavefunction = wavefunction_simulator.wavefunction(p)

            return wavefunction


        for i, p in enumerate(self.programs):
            p += ghz_state()
            ro = p.declare('ro', 'BIT', 3)

            # measure in bell basis
            p += CNOT(1, 0)
            p += H(1)

            p += MEASURE(0, ro[0])
            p += MEASURE(1, ro[1])

            p_copy = p.copy()
            result = self.qvm.run(p_copy, trials=NUM_TRIALS)[0]

            # choose bob or charlie to measure
            bob_or_charlie = int(np.random.choice([2, 3]))
            p += H(bob_or_charlie)
            p += MEASURE(bob_or_charlie, ro[2])

            self.programs[i] = p
            wavefunction = reconstruct(p, bob_or_charlie, result)

            print("Original alphas_betas: {}".format(self.alphas_betas[i]))
            print("Reconstructed alphas_betas: {}".format(wavefunction))

            curr_reconstructed = []
            for amplitude in wavefunction.amplitudes:
                if not np.allclose([amplitude], [0]):
                    curr_reconstructed.append(amplitude)
            curr_reconstructed = np.array(curr_reconstructed)
            curr_reconstructed = np.abs(curr_reconstructed)
            curr_alphas_betas = []
            for amplitude in np.abs(self.alphas_betas[i]):
                if not np.allclose([amplitude], [0]):
                    curr_alphas_betas.append(amplitude)

            # If an eavesdropper has entangled an ancilla qubit into the system,
            # errors will occur
            if not np.allclose(np.sort(np.real(curr_alphas_betas)),
                np.sort(np.real(curr_reconstructed))):
                raise Exception("Someone is eavesdropping...")
