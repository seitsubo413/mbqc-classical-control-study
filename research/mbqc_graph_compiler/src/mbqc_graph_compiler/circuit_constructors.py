"""
Circuit constructors for standard quantum algorithms in the JCZ gate model.

Each constructor returns (gates_list, num_qubits) where gates_list contains
JGate and CZGate objects representing the MBQC measurement pattern.
"""
from __future__ import annotations

import random

import numpy as np

from mbqc_graph_compiler.jcz_circuit import JCZCircuit


def construct_qft(nqubit: int) -> tuple[list, int]:
    jcz_circuit = JCZCircuit()
    for target in range(nqubit - 1):
        jcz_circuit.add_H(target)
        for control in range(target + 1, nqubit):
            phase = random.randint(0, 7)
            jcz_circuit.add_CRz(control, target, phase)
    jcz_circuit.add_H(nqubit - 1)
    return jcz_circuit.gates, nqubit


def construct_qaoa(
    nqubit: int,
    average_gate_num: float,
    sort: bool = True,
    ver: bool = True,
    draw: bool = False,
) -> tuple[list, int]:
    jcz_circuit = JCZCircuit()
    [jcz_circuit.add_J(qubit, random.randint(0, 7)) for qubit in range(nqubit)]
    [jcz_circuit.add_H(qubit) for qubit in range(nqubit)]

    all_possible_gates = [(i, j) for i in range(nqubit) for j in range(i + 1, nqubit)]
    gates = list(set(random.choices(all_possible_gates, k=int(len(all_possible_gates) * average_gate_num))))
    if sort:
        gates.sort()

    for gate in gates:
        jcz_circuit.add_CNOT(gate[1], gate[0])
        jcz_circuit.add_Rz(gate[0], random.randint(0, 7))
        jcz_circuit.add_CNOT(gate[1], gate[0])
    return jcz_circuit.gates, nqubit


def construct_bv(nqubit: int) -> tuple[list, int]:
    percentage = 0.5
    jcz_circuit = JCZCircuit()
    all_possible_gates = [(0, i) for i in range(1, nqubit)]
    from random import sample
    gates = list(set(sample(all_possible_gates, k=int(len(all_possible_gates) * percentage))))
    gates.sort()
    for gate in gates:
        jcz_circuit.add_CNOT(gate[1], gate[0])
    return jcz_circuit.gates, nqubit


def construct_vqe(nqubit: int) -> tuple[list, int]:
    jcz_circuit = JCZCircuit()
    for i in range(nqubit):
        for j in range(i + 1, nqubit):
            jcz_circuit.add_CNOT(i, j)
    return jcz_circuit.gates, nqubit


def construct_rca(nqubit: int) -> tuple[list, int]:
    jcz_circuit = JCZCircuit()
    for i in range(nqubit - 3):
        jcz_circuit.add_CNOT(i + 2, i + 1)
        jcz_circuit.add_CNOT(i + 2, i)
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
        jcz_circuit.add_Rz(i + 1, random.randint(0, 7))
        jcz_circuit.add_CNOT(i, i + 1)
        jcz_circuit.add_CNOT(i + 2, i)
        jcz_circuit.add_CNOT(i, i + 1)
    return jcz_circuit.gates, nqubit


def construct_qsim(
    nqubit: int,
    t: float = 1.0,
    trotter_steps: int = 1,
    Jx: float = 1.0,
    Jz: float = 1.0,
) -> tuple[list, int]:
    circuit = JCZCircuit()
    dt = t / trotter_steps

    for _ in range(trotter_steps):
        for i in range(nqubit - 1):
            circuit.add_CNOT(i, i + 1)
            circuit.add_Rz(i + 1, -2 * Jz * dt)
            circuit.add_CNOT(i, i + 1)

            circuit.add_H(i)
            circuit.add_H(i + 1)
            circuit.add_CNOT(i, i + 1)
            circuit.add_Rz(i + 1, -2 * Jx * dt)
            circuit.add_CNOT(i, i + 1)
            circuit.add_H(i)
            circuit.add_H(i + 1)

    return circuit.gates, nqubit


def construct_grover(nqubit: int) -> tuple[list, int]:
    circuit = JCZCircuit()

    for q in range(nqubit):
        circuit.add_H(q)

    for q in range(nqubit):
        circuit.add_X(q)

    mid = nqubit // 2
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

    for q in range(nqubit):
        circuit.add_H(q)
        circuit.add_X(q)

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


def construct_uccsd(nqubit: int, theta: float = 0.2, locality: int = 2) -> tuple[list, int]:
    circuit = JCZCircuit()

    for i in range(nqubit // 2):
        circuit.add_X(i)

    occ_orbs = list(range(nqubit // 2))
    virt_orbs = list(range(nqubit // 2, nqubit))
    for i in occ_orbs:
        for a in virt_orbs:
            circuit.add_H(i)
            circuit.add_H(a)
            circuit.add_CNOT(i, a)
            circuit.add_Rz(a, 2 * theta)
            circuit.add_CNOT(i, a)
            circuit.add_H(i)
            circuit.add_H(a)

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
