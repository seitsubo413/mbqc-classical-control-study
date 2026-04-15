import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


from benchmarks.generate_qec_benchmark import *
from qiskit import transpile
from qiskit.converters import circuit_to_dag


MF = 15
NM = 1
D = 20
depth_list_origin = {}
Alg_list = ['QFT', 'QSim', 'Grover']
P_list = [(2, 1, 1), (1, 1, 1), (1, 2, 2)]
for a in Alg_list:
    depth_list_origin[a] = []
    for P in P_list:
        for N in range(6, 61, 6):
            RL = N * 3

            if a == 'QFT':
                circ_origin = qec_qft(N)
            elif a == 'QSim':
                circ_origin = qec_qsim(N)
            else:
                circ_origin = qec_grover(N)

            circ = transpile(
                circ_origin,
                basis_gates=["cx", "h", "s", "t"], 
                optimization_level = 1
            )

            dag = circuit_to_dag(circ)
            avail_pre_qubits = []

            cur_qubit = 0
            depth = 0
            mg_index = 0
            ready_flag = {}
            for i in range(N):
                ready_flag[i] = 0
            while dag.depth():
                if depth % ((P[0] + P[1] + P[2]) * D * MF) == 0:
                    mg_index += P[2]
                if a == 'Grover' and P == (2, 1, 1):
                    if depth % ((P[0] + P[1] + P[2]) * N) > P[0] - 1 and depth % ((P[0] + P[1] + P[2]) * N) < P[0] + P[1]:
                        for i in range(N):
                            ready_flag[i] += 1
                else:
                    if depth % ((P[0] + P[1] + P[2]) * N) > P[1] - 1 and depth % ((P[0] + P[1] + P[2]) * N) < P[0] + P[1]:
                        for i in range(N):
                            ready_flag[i] += 1
                if depth % (P[0] + P[1] + P[2]) >= P[0] + P[1]:
                    if cur_qubit >= N:
                        cur_qubit = 0
                    
                    front_layer = dag.front_layer()
                    for node in front_layer:
                        if node.op.num_qubits == 1:
                            if ready_flag[node.qargs[0]._index] >= D:
                                if node.qargs[0]._index == cur_qubit:
                                    if node.op._name != 't':
                                        dag.remove_op_node(node)
                                        ready_flag[node.qargs[0]._index] -= D
                                    else:
                                        if mg_index:
                                            dag.remove_op_node(node)
                                            ready_flag[node.qargs[0]._index] -= D
                                            mg_index -= 1
                        else:
                            
                            q0 = node.qargs[0]._index
                            q1 = node.qargs[1]._index
                            if ready_flag[q0] >= D or ready_flag[q1] >= D:
                                if q0 == cur_qubit:
                                    if q1 in avail_pre_qubits:
                                        dag.remove_op_node(node)
                                        avail_pre_qubits.remove(q1)
                                        if ready_flag[q0] >= D:
                                            ready_flag[q0] -= D
                                        elif ready_flag[q1] >= D:
                                            ready_flag[q1] -= D
                                elif q1 == cur_qubit:
                                    if q0 in avail_pre_qubits:
                                        dag.remove_op_node(node)
                                        avail_pre_qubits.remove(q0)
                                        if ready_flag[q0] >= D:
                                            ready_flag[q0] -= D
                                        elif ready_flag[q1] >= D:
                                            ready_flag[q1] -= D
                    avail_pre_qubits.append(cur_qubit)
                    cur_qubit += 1
                depth += 1
            depth_list_origin[a].append(depth)
            print("finish", depth)
with open("data/qec_data.txt", 'w') as file:
    file.write(str(depth_list_origin) + '\n')