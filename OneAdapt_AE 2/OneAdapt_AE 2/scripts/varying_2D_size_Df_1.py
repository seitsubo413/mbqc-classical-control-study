import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# hardware size sense
from OneMem.Graph_State_Mapping import graph_state_mapping as gsm_dynamic
from Baseline.Generate_Benchmark import *

N_list = [8]
a_type = ["QAOA", "RCA", "VQE"]

HSize_list = []
layer_index_list = {}

Round = 1
RefreshBound = 1

for a in a_type:
    for N in N_list:
        layer_index_list[a + str(N ** 2)] = []

for h in range(2, 21, 2):   
    for a in a_type:
        for N in N_list:
            print(a, h)
            layer_index_all = 0
            layer1_index_all = 0
            for r in range(Round):
                inter_edges_list, layer_index0, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm_dynamic(h, N ** 2, a, True, RefreshBound, True, True, 0.4)
                layer_index_all += layer_index0
            layer_index_list[a + str(N ** 2)].append(layer_index_all / Round)
    HSize_list.append(h)

with open("data/h_1.txt", 'w') as file:
    file.write(str(HSize_list) + '\n')
    file.write(str(layer_index_list) + '\n')