import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


from Build_Cluster.Build_Cluster import *
from OneMem.Graph_State_Mapping import graph_state_mapping as gsm_onemem

RefreshBound = 40
Row = 8
P = 0.75
AverageL = 24
a_list = ['QAOA', 'RCA', 'VQE']
time_index_map = {}
layer_index_map = {}

for a in a_list:
    time_index_map[a] = []
    layer_index_map[a] = []
    for NQubit in range(4, 65, 8):    
        N = AverageL * Row
        inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm_onemem(Row, NQubit, a, True, RefreshBound, True, True, 0.4)
        time_index_braiding, max_interspace = build_braiding_cluster(Row, NQubit, layer_index, swap_map, N, P, AverageL)
        time_index_map[a].append(time_index_braiding)
        layer_index_map[a].append(layer_index)

with open("data/pl_ratio.txt", 'w') as file:
    file.write(str(time_index_map) + '\n')
    file.write(str(layer_index_map) + '\n')