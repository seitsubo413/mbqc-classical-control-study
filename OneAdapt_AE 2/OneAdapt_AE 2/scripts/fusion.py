import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from Build_Cluster.Build_Cluster import *
from OneMem.Graph_State_Mapping import graph_state_mapping as gsm_onemem


NQubit = 36

algorithm_type = ['QAOA', 'VQE', 'RCA']
RefreshBound = 30
fusion_succ_list = [0.66, 0.69, 0.72, 0.75, 0.78]
stripe_length = [40, 28, 25, 20, 18]
algorithm_type = ['QAOA', 'VQE', 'RCA']

rsl_depth_map = {}

for a in algorithm_type:
    rsl_depth_map[a] = []
    for i in range(5):
        inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm_onemem(84 // stripe_length[i], NQubit, a, True, RefreshBound, True, True, 0.4)
        time_index_braiding, max_interspace = build_braiding_cluster(84 // stripe_length[i], NQubit, layer_index, swap_map, 84, fusion_succ_list[i], stripe_length[i])
        rsl_depth_map[a].append(time_index_braiding)
    print(rsl_depth_map)

with open("data/fusion_succ_sensitivity.txt", 'w') as file:
    file.write(str(fusion_succ_list) + '\n')
    file.write(str(rsl_depth_map) + '\n')