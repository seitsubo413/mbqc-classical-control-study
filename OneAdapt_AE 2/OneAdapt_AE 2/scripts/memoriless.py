import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from OneMem.Graph_State_Mapping import graph_state_mapping as gsm_dynamic
from Baseline.Generate_Benchmark import *

headers = ["Benchmark Name", "Qiskit Depth", "Qiskit Braiding Depth", 'Braiding Qiskit vs Qiskit', 'Memoriless OneMem Depth', 'OneMem vs Qiskit']

N_list = [6, 8, 10]
algorithm_type = ["QAOA", "RCA", "VQE"]
Round = 1

qiskit_depth_list = {}
qiskit_braiding_depth_list = {}
onemem_layer_index_list = {}

for a in algorithm_type:
    qiskit_depth_list[a] = []
    qiskit_braiding_depth_list[a] = []
    onemem_layer_index_list[a] = []

for N in N_list:
    for a in algorithm_type:
        qiskit_depth_all = 0
        qiskit_braiding_depth_all = 0
        onemem_layer_index_all = 0

        for r in range(Round):
            braiding_depth, original_depth, swap_gate_depths_qubits  = generate_benchmark(N, N, N ** 2, a)
            qiskit_depth_all += original_depth
            qiskit_braiding_depth_all += braiding_depth

            inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm_dynamic(N, N ** 2, a, True, 1, True, True, 0.4)
            onemem_layer_index_all += layer_index

        qiskit_depth_list[a].append(qiskit_depth_all / Round)
        qiskit_braiding_depth_list[a].append(qiskit_braiding_depth_all / Round)
        
        onemem_layer_index_list[a].append(onemem_layer_index_all / Round)


with open("data/memoriless.txt", 'w') as file:
    file.write(str(qiskit_depth_list) + '\n')
    file.write(str(qiskit_braiding_depth_list) + '\n')
    file.write(str(onemem_layer_index_list) + '\n')