# alpha = phase * 1/4 pi
# convert all gates into JGate and CZGate
class JGate:
    def __init__(self, qubit: int, phase: float) -> None:
        self.qubit = qubit
        self.phase = phase

    def type(self) -> str:
        return "J"


class CZGate:
    def __init__(self, qubit1: int, qubit2: int) -> None:
        self.qubit1 = qubit1
        self.qubit2 = qubit2

    def type(self) -> str:
        return "CZ"


class JCZCircuit:
    def __init__(self) -> None:
        self.qubits: list[int] = []
        self.gates: list[JGate | CZGate] = []

    def qubits_init(self, qubits: list[int]) -> None:
        self.qubits = qubits

    def add_J(self, qubit: int, phase: float) -> None:
        self.gates.append(JGate(qubit, phase))

    def add_H(self, qubit: int) -> None:
        self.gates.append(JGate(qubit, 0))

    def add_X(self, qubit: int) -> None:
        self.gates.append(JGate(qubit, 0))
        self.gates.append(JGate(qubit, 4))

    def add_Z(self, qubit: int) -> None:
        self.gates.append(JGate(qubit, 4))
        self.gates.append(JGate(qubit, 0))

    def add_T(self, qubit: int) -> None:
        self.gates.append(JGate(qubit, 1))
        self.gates.append(JGate(qubit, 0))

    def add_S(self, qubit: int) -> None:
        self.gates.append(JGate(qubit, 2))
        self.gates.append(JGate(qubit, 0))

    def add_Rz(self, qubit: int, phase: float) -> None:
        self.gates.append(JGate(qubit, phase))
        self.gates.append(JGate(qubit, 0))

    def add_CZ(self, qubit1: int, qubit2: int) -> None:
        self.gates.append(CZGate(qubit1, qubit2))

    def add_CNOT(self, qubit1: int, qubit2: int) -> None:
        self.add_H(qubit2)
        self.add_CZ(qubit1, qubit2)
        self.add_H(qubit2)

    def add_CRz(self, qubit1: int, qubit2: int, phase: float) -> None:
        self.add_Rz(qubit1, phase)
        self.add_Rz(qubit2, phase)
        self.add_CNOT(qubit1, qubit2)
        self.add_Rz(qubit2, phase)
        self.add_CNOT(qubit1, qubit2)
