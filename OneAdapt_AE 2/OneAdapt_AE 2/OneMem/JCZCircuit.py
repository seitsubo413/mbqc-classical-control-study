# alpha = phase * 1/4 pi
# convert all gate into JGate and CZGate
class JGate:
    def __init__(self, qubit, phase):
        self.qubit = qubit
        self.phase = phase
    
    def type(self):
        return "J"
    
class CZGate:
    def __init__(self, qubit1, qubit2):
        self.qubit1 = qubit1
        self.qubit2 = qubit2
    
    def type(self):
        return "CZ"


class JCZCircuit:
    def __init__(self):
        self.qubits = []
        self.gates = []

    def qubits_init(self, qubits):
        self.qubits = qubits

    def add_J(self, qubit, phase):
        self.gates.append(JGate(qubit, phase))

    def add_H(self, qubit):
        self.gates.append(JGate(qubit, 4))

    def add_X(self, qubit):
        self.gates.append(JGate(qubit, 0))
        self.gates.append(JGate(qubit, 4))
    
    def add_Z(self, qubit):
        self.gates.append(JGate(qubit, 4))
        self.gates.append(JGate(qubit, 0))
    
    def add_T(self, qubit):
        self.gates.append(JGate(qubit, 1))
        self.gates.append(JGate(qubit, 0))
    
    def add_S(self, qubit):
        self.gates.append(JGate(qubit, 2))
        self.gates.append(JGate(qubit, 0))
    
    def add_Rz(self, qubit, phase):
        self.gates.append(JGate(qubit, phase))
        self.gates.append(JGate(qubit, 0))

    def add_CZ(self, qubit1, qubit2):
        self.gates.append(CZGate(qubit1, qubit2))

    def add_CNOT(self, qubit1, qubit2):
        self.add_H(qubit2)
        self.add_CZ(qubit1, qubit2)
        self.add_H(qubit2)
    
    def add_CRz(self, qubit1, qubit2, phase):
        self.add_Rz(qubit1, phase)
        self.add_Rz(qubit2, phase)
        self.add_CNOT(qubit1,qubit2)
        self.add_Rz(qubit2, phase)
        self.add_CNOT(qubit1,qubit2) 
    