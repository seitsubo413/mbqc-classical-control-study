import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from OneMem.Graph_State_Mapping import graph_state_mapping as gsm_dynamic
from Baseline.Generate_Benchmark import *
import math

headers = ["Benchmark Name", "Qiskit Depth", "Qiskit Braiding Depth", 'Braiding Qiskit vs Qiskit', 'Memoriless OneMem Depth', 'OneMem vs Qiskit']

N_list = [24, 26, 60]
algorithm_type = ["UCCSD"]
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
            braiding_depth, original_depth, swap_gate_depths_qubits  = generate_benchmark(math.ceil(math.sqrt(N)), math.ceil(math.sqrt(N)), N, a)
            qiskit_depth_all += original_depth
            qiskit_braiding_depth_all += braiding_depth

            inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm_dynamic(math.ceil(math.sqrt(N)), N, a, True, 1, True, True, 0.4)
            onemem_layer_index_all += layer_index

        qiskit_depth_list[a].append(qiskit_depth_all / Round)
        qiskit_braiding_depth_list[a].append(qiskit_braiding_depth_all / Round)
        
        onemem_layer_index_list[a].append(onemem_layer_index_all / Round)

with open("data/memoriless_uccsd.txt", 'w') as file:
    file.write(str(qiskit_depth_list) + '\n')
    file.write(str(qiskit_braiding_depth_list) + '\n')
    file.write(str(onemem_layer_index_list) + '\n')