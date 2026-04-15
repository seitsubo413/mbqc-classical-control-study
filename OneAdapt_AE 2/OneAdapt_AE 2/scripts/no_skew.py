import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


from No_Skew.Graph_State_Mapping import graph_state_mapping as gsm
from OneMem.Graph_State_Mapping import graph_state_mapping as gsm_origin

N = 8

depth_list = {}
depth_list_origin = {}
for a in ['QAOA', 'RCA', 'VQE']:
    depth_list[a] = []
    depth_list_origin[a] = []
    for RefreshBound  in [1, 2, 3, 5, 10]:
        inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm(N, N ** 2, a, True, RefreshBound, True, True, 0.25)
        depth_list[a].append(layer_index)
        inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm_origin(N, N ** 2, a, True, RefreshBound, True, True, 0.4)
        depth_list_origin[a].append(layer_index)


with open("data/no_skew_table.txt", 'w') as file:
    file.write(str(depth_list) + '\n')
    file.write(str(depth_list_origin) + '\n')