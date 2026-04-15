from Baseline.Get_Coupling_Map import get_coupling_map
from Baseline.Get_Swap_Depth import *
from Baseline.Benchmark_Circuits import *


from qiskit import transpile
from qiskit.transpiler import CouplingMap

def generate_benchmark(Row, Col, NQubit, a):
    coupling_map = get_coupling_map(Row, Col, False)
    if a == 'QAOA':
        qiskit_circuit = genQiskitQAOA(NQubit  , Row * Col)
    elif a == 'QFT':
        qiskit_circuit = genQiskitQFT(NQubit  , Row * Col)
    elif a == 'VQE':
        qiskit_circuit = genQiskitVQE(NQubit  , Row * Col)
    elif a == 'RCA':
        qiskit_circuit = genQiskitRCA(NQubit  , Row * Col)
    elif a == 'BV':
        qiskit_circuit = genQiskitBV(NQubit  , Row * Col)
    elif a == 'QSIM':
        qiskit_circuit = genQiskitQSIM(NQubit  , Row * Col)
    elif a == 'UCCSD':
        qiskit_circuit = genQiskitUCCSD(NQubit)
        
    transpiled_circuit = transpile(qiskit_circuit, basis_gates = ['cz', 'rz', 'h', 'swap'], coupling_map=CouplingMap(coupling_map), routing_method = 'sabre')

    swap_gate_depths_qubits, qubit_depths = get_swap_depths(transpiled_circuit)

    swap_index = 0
    for depth, qubits in swap_gate_depths_qubits.items():
        print("swap" + str(swap_index) + ":\n depth", depth,'\n qubits:', qubits)
        swap_index += 1

 
    braiding_depth = max(get_depths(transpiled_circuit).values())
    print("braiding depth", braiding_depth)
    swap_decomposed_circuit = transpile(qiskit_circuit, basis_gates = ['cz', 'rz', 'h'], coupling_map=CouplingMap(coupling_map), routing_method = 'sabre')
    qubit_depths = get_depths(swap_decomposed_circuit)
    original_depth = max(qubit_depths.values())
    print("decomposed depth:", original_depth)

    return braiding_depth, original_depth, swap_gate_depths_qubits