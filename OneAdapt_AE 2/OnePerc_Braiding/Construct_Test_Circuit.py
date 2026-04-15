import pyzx as zx
import random
from OnePerc.JCZCircuit import *
from qiskit import QuantumCircuit
from random import choices, sample

def generate_circuit(nqubit, depth):
    circuit = zx.generate.CNOT_HAD_PHASE_circuit(qubits=nqubit,depth=depth,clifford=False)
    qubits = []
    for i in range(nqubit):
        qubits.append(i)
    jcz_circuit = JCZCircuit()
    jcz_circuit.qubits_init(qubits)
    for gate in circuit.gates:
        if gate.name == "HAD":
            jcz_circuit.add_H(int(str(gate)[4:-1]))
        elif gate.name == "CNOT":
            gate_split = str(gate).split(',')
            qubit1 = int(gate_split[0][5:])
            qubit2 = int(gate_split[1][0:-1])
            jcz_circuit.add_CNOT(qubit1, qubit2)
        elif gate.name == "T":
            jcz_circuit.add_T(int(str(gate)[2:-1]))

    return  jcz_circuit.gates, nqubit

def construct_qft(nqubit):
    jcz_circuit = JCZCircuit()
    for target in range(nqubit - 1):
        jcz_circuit.add_H(target)
        for control in range(target + 1, nqubit):
            phase = random.randint(0, 7)
            jcz_circuit.add_CRz(control, target, phase)
    jcz_circuit.add_H(nqubit - 1)
    return jcz_circuit.gates, nqubit

def construct_qaoa(nqubit, average_gate_num, sort=True, ver=True, draw=False):
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_J(qubit, random.randint(0, 7)) for qubit in range(nqubit)]
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]
    
    all_possible_gates = [(i,j) for i in range(nqubit) for j in range(i+1, nqubit)]
    gates = list(set(random.choices(all_possible_gates, k= int(len(all_possible_gates)*average_gate_num))))
    if sort:
        gates.sort() 

    for gate in gates:
        jcz_circuit.add_CNOT(gate[1], gate[0])
        jcz_circuit.add_Rz(gate[0], random.randint(0, 7))
        jcz_circuit.add_CNOT(gate[1], gate[0])
    return jcz_circuit.gates, nqubit

def construct_bv(nqubit):
    percentage=0.5
    jcz_circuit = JCZCircuit()
    all_possible_gates = [(0,i) for i in range(1,nqubit)]
    gates = list(set(sample(all_possible_gates, k=int(len(all_possible_gates)*percentage))))
    gates.sort()
    for gate in gates:
        jcz_circuit.add_CNOT(gate[1], gate[0])
    return jcz_circuit.gates, nqubit

def construct_vqe(nqubit):
    jcz_circuit = JCZCircuit()
    for i in range(nqubit):
        for j in range(i+1, nqubit):
            jcz_circuit.add_CNOT(i, j)

    return jcz_circuit.gates, nqubit

def construct_rca(nqubit):
    jcz_circuit = JCZCircuit()
    #qubit_num = 3 * n + 1
    for i in range(nqubit - 3):
        jcz_circuit.add_CNOT(i + 2,i + 1)
        jcz_circuit.add_CNOT(i + 2,i)
        jcz_circuit.add_H(i + 2)
        jcz_circuit.add_CNOT(i + 1, i + 2)
        jcz_circuit.add_Rz(i + 2, random.randint(0, 7))
        jcz_circuit.add_CNOT(i, i + 2)
        jcz_circuit.add_Rz(i + 2, random.randint(0, 7))
        jcz_circuit.add_CNOT(i + 1, i + 2)
        jcz_circuit.add_Rz(i + 2, random.randint(0, 7))
        jcz_circuit.add_CNOT(i, i + 2)
        
        jcz_circuit.add_Rz(i + 1, random.randint(0, 7))
        jcz_circuit.add_Rz(i + 2, random.randint(0, 7))
        jcz_circuit.add_H(i + 2)
        
        jcz_circuit.add_CNOT(i, i + 1)
        jcz_circuit.add_Rz(i, random.randint(0, 7))
        jcz_circuit.add_Rz(i + 1, random.randint(0, 7))
        jcz_circuit.add_CNOT(i, i + 1)
    jcz_circuit.add_CNOT(nqubit - 2, nqubit - 1)
    for i in range(nqubit - 4, -1, -1):
        jcz_circuit.add_H(i + 2)
        jcz_circuit.add_CNOT(i + 1, i + 2)
        jcz_circuit.add_Rz(i + 2, random.randint(0, 7))
        jcz_circuit.add_CNOT(i, i + 2)
        jcz_circuit.add_Rz(i + 2, random.randint(0, 7))
        jcz_circuit.add_CNOT(i + 1, i + 2)
        jcz_circuit.add_Rz(i + 2, random.randint(0, 7))
        jcz_circuit.add_CNOT(i, i + 2)
        
        jcz_circuit.add_Rz(i + 1, random.randint(0, 7))
        jcz_circuit.add_Rz(i + 2, random.randint(0, 7))
        jcz_circuit.add_H(i + 2)
        
        jcz_circuit.add_CNOT(i, i + 1)
        jcz_circuit.add_Rz(i, random.randint(0, 7))
        jcz_circuit.add_Rz(i + 1,random.randint(0, 7))
        jcz_circuit.add_CNOT(i, i + 1)
        jcz_circuit.add_CNOT(i + 2,i)
        jcz_circuit.add_CNOT(i ,i + 1)

    return jcz_circuit.gates, nqubit

def construct_qsim(nqubit, t=1.0, trotter_steps=1, Jx=1.0, Jz=1.0):

    circuit = JCZCircuit()
    dt = t / trotter_steps

    for _ in range(trotter_steps):
        for i in range(nqubit - 1):
            # ---- ZZ interaction (decompose e^{-i Jz Z⊗Z dt}) ----
            circuit.add_CNOT(i, i+1)
            circuit.add_Rz(i+1, -2 * Jz * dt)
            circuit.add_CNOT(i, i+1)

            # ---- XX interaction (decompose e^{-i Jx X⊗X dt}) ----
            circuit.add_H(i)
            circuit.add_H(i+1)
            circuit.add_CNOT(i, i+1)
            circuit.add_Rz(i+1, -2 * Jx * dt)
            circuit.add_CNOT(i, i+1)
            circuit.add_H(i)
            circuit.add_H(i+1)


    return circuit.gates, nqubit

import numpy as np
def construct_grover(nqubit):

    circuit = JCZCircuit()

    # Step 1: Hadamard to all qubits
    for q in range(nqubit):
        circuit.add_H(q)

    # ---- Oracle for |11...1⟩ ----
    for q in range(nqubit):
        circuit.add_X(q)

    # Implement multi-controlled Z using CNOT chain around H-RZ-H on center qubit
    mid = nqubit // 2
    # Forward CNOT chain
    for i in range(mid - 1, -1, -1):
        circuit.add_CNOT(i, i + 1)
    for i in range(mid + 1, nqubit):
        circuit.add_CNOT(i, i - 1)

    # H-RZ(-π)-H on center
    circuit.add_H(mid)
    circuit.add_Rz(mid, -np.pi)
    circuit.add_H(mid)

    # Backward CNOT chain
    for i in range(mid + 1, nqubit):
        circuit.add_CNOT(i, i - 1)
    for i in range(mid - 1, -1, -1):
        circuit.add_CNOT(i, i + 1)

    for q in range(nqubit):
        circuit.add_X(q)

    # ---- Diffuser ----
    for q in range(nqubit):
        circuit.add_H(q)
        circuit.add_X(q)

    # Same controlled-Z structure
    for i in range(mid - 1, -1, -1):
        circuit.add_CNOT(i, i + 1)
    for i in range(mid + 1, nqubit):
        circuit.add_CNOT(i, i - 1)

    circuit.add_H(mid)
    circuit.add_Rz(mid, -np.pi)
    circuit.add_H(mid)

    for i in range(mid + 1, nqubit):
        circuit.add_CNOT(i, i - 1)
    for i in range(mid - 1, -1, -1):
        circuit.add_CNOT(i, i + 1)

    for q in range(nqubit):
        circuit.add_X(q)
        circuit.add_H(q)


    return circuit.gates, nqubit

# def construct_uccsd(nqubit, theta=0.2):
#     circuit = JCZCircuit()

#     # 1. Hartree-Fock reference (fill first half of qubits)
#     for i in range(nqubit // 2):
#         circuit.add_X(i)

#     # 2. Simulated excitation terms (e.g., e^{-iθ P} for some Pauli strings)
#     # Here we use several pairwise XX + YY rotations, decomposed into H/CNOT/Rz

#     for i in range(nqubit - 3):
#         q0, q1, q2, q3 = i, i+1, i+2, i+3

#         # Basis change for XX (H-H)
#         circuit.add_H(q0)
#         circuit.add_H(q2)

#         # Entangle XX
#         circuit.add_CNOT(q0, q2)
#         circuit.add_Rz(q2, 2 * theta)
#         circuit.add_CNOT(q0, q2)

#         # Un-H
#         circuit.add_H(q0)
#         circuit.add_H(q2)

#         # Basis change for YY (Sdg-H), but approximate with Rz+H
#         circuit.add_Rz(q1, np.pi/2)
#         circuit.add_H(q1)
#         circuit.add_Rz(q3, np.pi/2)
#         circuit.add_H(q3)

#         # Entangle YY
#         circuit.add_CNOT(q1, q3)
#         circuit.add_Rz(q3, 2 * theta)
#         circuit.add_CNOT(q1, q3)

#         # Undo
#         circuit.add_H(q1)
#         circuit.add_Rz(q1, -np.pi/2)
#         circuit.add_H(q3)
#         circuit.add_Rz(q3, -np.pi/2)


#     return circuit.gates, nqubit

# def construct_uccsd(nqubit, theta=0.2):
#     circuit = JCZCircuit()

#     # 1. Hartree-Fock reference state: fill lowest nqubit//2 orbitals
#     for i in range(nqubit // 2):
#         circuit.add_X(i)  # HF state: occupy the first half

#     # 2. Generate all single excitations: i (occ) → a (virt)
#     occ_orbs = list(range(nqubit // 2))
#     virt_orbs = list(range(nqubit // 2, nqubit))
#     for i in occ_orbs:
#         for a in virt_orbs:
#             # Approximate e^{-iθ(X_i X_a + Y_i Y_a)} by hand-crafted sequence
#             circuit.add_H(i)
#             circuit.add_H(a)
#             circuit.add_CNOT(i, a)
#             circuit.add_Rz(a, 2 * theta)
#             circuit.add_CNOT(i, a)
#             circuit.add_H(i)
#             circuit.add_H(a)

#             # YY part
#             circuit.add_Rz(i, np.pi / 2)
#             circuit.add_H(i)
#             circuit.add_Rz(a, np.pi / 2)
#             circuit.add_H(a)
#             circuit.add_CNOT(i, a)
#             circuit.add_Rz(a, 2 * theta)
#             circuit.add_CNOT(i, a)
#             circuit.add_H(i)
#             circuit.add_Rz(i, -np.pi / 2)
#             circuit.add_H(a)
#             circuit.add_Rz(a, -np.pi / 2)

#     # 3. Generate all double excitations: (i,j) (occ) → (a,b) (virt)
#     for i in occ_orbs:
#         for j in occ_orbs:
#             if i >= j: continue
#             for a in virt_orbs:
#                 for b in virt_orbs:
#                     if a >= b: continue
#                     # Double excitation approx: apply entangling gates across i-a and j-b
#                     for (q1, q2) in [(i, a), (j, b)]:
#                         circuit.add_H(q1)
#                         circuit.add_H(q2)
#                         circuit.add_CNOT(q1, q2)
#                         circuit.add_Rz(q2, 2 * theta)
#                         circuit.add_CNOT(q1, q2)
#                         circuit.add_H(q1)
#                         circuit.add_H(q2)

#                         circuit.add_Rz(q1, np.pi / 2)
#                         circuit.add_H(q1)
#                         circuit.add_Rz(q2, np.pi / 2)
#                         circuit.add_H(q2)
#                         circuit.add_CNOT(q1, q2)
#                         circuit.add_Rz(q2, 2 * theta)
#                         circuit.add_CNOT(q1, q2)
#                         circuit.add_H(q1)
#                         circuit.add_Rz(q1, -np.pi / 2)
#                         circuit.add_H(q2)
#                         circuit.add_Rz(q2, -np.pi / 2)

#     return circuit.gates, nqubit

def construct_uccsd(nqubit, theta=0.2, locality=2):
    circuit = JCZCircuit()

    # Step 1: Hartree-Fock state preparation (occupy first half)
    for i in range(nqubit // 2):
        circuit.add_X(i)

    # Step 2: Apply a few local single excitations i → a (occupied → virtual)
    occ_orbs = list(range(nqubit // 2))
    virt_orbs = list(range(nqubit // 2, nqubit))
    for i in occ_orbs:
        for a in virt_orbs:
            # if abs(i - a) > locality:
            #     continue  # locality truncation

            # XX rotation component
            circuit.add_H(i)
            circuit.add_H(a)
            circuit.add_CNOT(i, a)
            circuit.add_Rz(a, 2 * theta)
            circuit.add_CNOT(i, a)
            circuit.add_H(i)
            circuit.add_H(a)

            # YY rotation component
            circuit.add_Rz(i, np.pi / 2)
            circuit.add_H(i)
            circuit.add_Rz(a, np.pi / 2)
            circuit.add_H(a)
            circuit.add_CNOT(i, a)
            circuit.add_Rz(a, 2 * theta)
            circuit.add_CNOT(i, a)
            circuit.add_H(i)
            circuit.add_Rz(i, -np.pi / 2)
            circuit.add_H(a)
            circuit.add_Rz(a, -np.pi / 2)

    return circuit.gates, nqubit