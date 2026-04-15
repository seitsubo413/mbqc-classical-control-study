import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from OneMem.Graph_State_Mapping import graph_state_mapping as gsm_onemem

RefreshBound = 20
N = 6
onemem_actual_life_time_list = {}
onemem_refresh_layer_index_list = {}
max_onemem_measure_delay_list = {}

for a in ["QAOA", "RCA", "VQE"]:
    onemem_actual_life_time_list[a] = []
    onemem_refresh_layer_index_list[a] = []
    max_onemem_measure_delay_list[a] = []
    for P_const in [0.1, 0.2, 0.3, 0.4, 0.6]: 
        inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm_onemem(N, N ** 2, a, True, RefreshBound, True, True, P_const)
        onemem_actual_life_time_list[a].append(life_time)
        onemem_refresh_layer_index_list[a].append(layer_index)
        max_onemem_measure_delay_list[a].append(0)


with open("data/p_sense.txt", 'w') as file:
    file.write(str(onemem_actual_life_time_list) + '\n')
    file.write(str(onemem_refresh_layer_index_list) + '\n')
    file.write(str(max_onemem_measure_delay_list) + '\n')