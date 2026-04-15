from qiskit import QuantumCircuit

def qec_qft(n):
    qc = QuantumCircuit(n)
    for i in range(n):
        qc.h(i)  # Hadamard gate
        for j in range(i+1, n):
            qc.cx(i, j)
            qc.sdg(j)  # S† gate
            qc.cx(i, j)
            qc.t(j)  # T gate (for controlled phase)
    
    return qc

def qec_grover(n):
    qc = QuantumCircuit(n)
    
    # Apply Hadamard to all qubits
    for i in range(n):
        qc.h(i)
    
    # Oracle (example for |11...1> state) using CX, S, and T gates
    # qc.barrier()
    for i in range(n):
        qc.x(i)
    qc.h(n-1)
    for i in range(n-1):
        qc.cx(i, n-1)
    qc.s(n-1)
    for i in range(n-1):
        qc.cx(i, n-1)
    qc.h(n-1)
    for i in range(n):
        qc.x(i)
    # qc.barrier()
    
    # Diffuser using only CX, S, T, and H gates
    for i in range(n):
        qc.h(i)
        qc.x(i)
    qc.h(n-1)
    for i in range(n-1):
        qc.cx(i, n-1)
    qc.s(n-1)
    for i in range(n-1):
        qc.cx(i, n-1)
    qc.h(n-1)
    for i in range(n):
        qc.x(i)
        qc.h(i)
    
    return qc

def qec_qsim(n):
    qc = QuantumCircuit(n)
    
    # Initial Hadamard layer
    for i in range(n):
        qc.h(i)
    
    # QSim core operations using CX, S, T, and H gates
    # qc.barrier()
    for i in range(n-1):
        qc.cx(i, i+1)
        qc.s(i+1)
        qc.t(i)
        qc.cx(i, i+1)
    # qc.barrier()
    
    # Final Hadamard layer
    for i in range(n):
        qc.h(i)
    
    return qc