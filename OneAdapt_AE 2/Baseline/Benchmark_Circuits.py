from qiskit import QuantumCircuit
from random import sample
from math import *
import random

def genQiskitBV(program_qubit_num, hardware_qubit_num, percentage=0.5):
    all_possible_gates = [(0,i) for i in range(1,program_qubit_num)]
    gates = list(set(sample(all_possible_gates, k=int(len(all_possible_gates)*percentage))))
    gates.sort()
    print("{}/{} gates selected : {} ... {}".format(len(gates), len(all_possible_gates), gates[:10], gates[-10:]))
    
    qiskit_circuit = QuantumCircuit(hardware_qubit_num)
    for c,t in gates:
        qiskit_circuit.cx(c,t)
    return qiskit_circuit
    

def genQiskitQAOA(program_qubit_num, hardware_qubit_num, percentage=0.5):
    all_possible_gates = [(i,j) for i in range(program_qubit_num) for j in range(i+1, program_qubit_num)]
    gates = list(set(sample(all_possible_gates, k=int(len(all_possible_gates)*percentage))))
    gates.sort()
    print("{}/{} gates selected : {} ... {}".format(len(gates), len(all_possible_gates), gates[:10], gates[-10:]))
    
    qiskit_circuit = QuantumCircuit(hardware_qubit_num)
    for c,t in gates:
        qiskit_circuit.cx(c,t)
        qiskit_circuit.rz(pi/3, t)
        qiskit_circuit.cx(c,t)
    return qiskit_circuit


def qiskit_control_rotation(qiskit_circuit, c, r):
    qiskit_circuit.rz(pi/3, c)
    qiskit_circuit.rz(pi/3, r)
    qiskit_circuit.cx(c,r)
    qiskit_circuit.rz(pi/3, r)
    qiskit_circuit.cx(c,r)

def genQiskitQFT(program_qubit_num, hardware_qubit_num):
    qiskit_circuit = QuantumCircuit(hardware_qubit_num)
    for target in range(program_qubit_num - 1):
        qiskit_circuit.h(target)
        for control in range(target + 1, program_qubit_num):
            qiskit_circuit.rz(pi/3, control)
            qiskit_circuit.rz(pi/3, target)
            qiskit_circuit.h(target)
            qiskit_circuit.cz(control, target)
            qiskit_circuit.h(target)
            qiskit_circuit.rz(pi/3, target)
            qiskit_circuit.h(target)
            qiskit_circuit.cz(control, target)
            qiskit_circuit.h(target)
    qiskit_circuit.h(program_qubit_num - 1)
    return qiskit_circuit


def genQiskitVQE(program_qubit_num, hardware_qubit_num):
    qiskit_circuit = QuantumCircuit(hardware_qubit_num)
    for i in range(program_qubit_num):
        for j in range(i+1, program_qubit_num):
            qiskit_circuit.cx(i,j)
    print('{} gates'.format(program_qubit_num**2/2))
    return qiskit_circuit

def genQiskitRCA(program_qubit_num, hardware_qubit_num):
    qiskit_circuit = QuantumCircuit(hardware_qubit_num)
    #qubit_num = 3 * n + 1
    for i in range(program_qubit_num - 3):
        qiskit_circuit.cx(i + 2,i + 1)
        qiskit_circuit.cx(i + 2,i)
        qiskit_circuit.h(i + 2)
        qiskit_circuit.cx(i + 1, i + 2)
        qiskit_circuit.rz(pi / 3, i + 2)
        qiskit_circuit.cx(i, i + 2)
        qiskit_circuit.rz(pi / 3, i + 2)
        qiskit_circuit.cx(i + 1, i + 2)
        qiskit_circuit.rz(pi / 3, i + 2)
        qiskit_circuit.cx(i, i + 2)
        
        qiskit_circuit.rz(pi / 3, i + 1)
        qiskit_circuit.rz(pi / 3, i + 2)
        qiskit_circuit.h(i + 2)
        
        qiskit_circuit.cx(i, i + 1)
        qiskit_circuit.rz(pi / 3, i)
        qiskit_circuit.rz(pi / 3, i + 1)
        qiskit_circuit.cx(i, i + 1)
    qiskit_circuit.cx(program_qubit_num - 2, program_qubit_num - 1)
    for i in range(program_qubit_num - 4, -1, -1):
        qiskit_circuit.h(i + 2)
        qiskit_circuit.cx(i + 1, i + 2)
        qiskit_circuit.rz(pi / 3, i + 2)
        qiskit_circuit.cx(i, i + 2)
        qiskit_circuit.rz(pi / 3, i + 2)
        qiskit_circuit.cx(i + 1, i + 2)
        qiskit_circuit.rz(pi / 3, i + 2)
        qiskit_circuit.cx(i, i + 2)
        
        qiskit_circuit.rz(pi / 3, i + 1)
        qiskit_circuit.rz(pi / 3, i + 2)
        qiskit_circuit.h(i + 2)
        
        qiskit_circuit.cx(i, i + 1)
        qiskit_circuit.rz(pi / 3, i)
        qiskit_circuit.rz(pi / 3, i + 1)
        qiskit_circuit.cx(i, i + 1)
        qiskit_circuit.cx(i + 2,i)
        qiskit_circuit.cx(i ,i + 1)

    return qiskit_circuit

from qiskit.circuit.library import RZZGate, RXXGate

def genQiskitQSIM(program_qubit_num, hardware_qubit_num, t=1.0, trotter_steps=1):
    if program_qubit_num > hardware_qubit_num:
        raise ValueError("program_qubit_num exceeds hardware_qubit_num.")

    qc = QuantumCircuit(hardware_qubit_num)
    dt = t / trotter_steps

    for _ in range(trotter_steps):
        for i in range(program_qubit_num - 1):
            # XX interaction
            qc.append(RXXGate(2 * dt), [i, i + 1])
            # ZZ interaction
            qc.append(RZZGate(2 * dt), [i, i + 1])

    return qc

import numpy as np
def genQiskitUCCSD(nqubit, theta=0.2, locality=2):
    circuit = QuantumCircuit(nqubit)

    # Step 1: Hartree-Fock state preparation (occupy first half)
    for i in range(nqubit // 2):
        circuit.x(i)

    # Step 2: Apply a few local single excitations i → a (occupied → virtual)
    occ_orbs = list(range(nqubit // 2))
    virt_orbs = list(range(nqubit // 2, nqubit))
    for i in occ_orbs:
        for a in virt_orbs:
            # if abs(i - a) > locality:
            #     continue  # locality truncation

            # XX rotation component
            circuit.h(i)
            circuit.h(a)
            circuit.cx(i, a)
            circuit.rz(np.pi / 3, a)
            circuit.cx(i, a)
            circuit.h(i)
            circuit.h(a)

            # YY rotation component
            circuit.rz(np.pi / 2, i)
            circuit.h(i)
            circuit.rz(np.pi / 2, a)
            circuit.h(a)
            circuit.cx(i, a)
            circuit.rz(2 * theta, a)
            circuit.cx(i, a)
            circuit.h(i)
            circuit.rz(-np.pi / 2, i)
            circuit.h(a)
            circuit.rz(-np.pi / 2, a)

    return circuit