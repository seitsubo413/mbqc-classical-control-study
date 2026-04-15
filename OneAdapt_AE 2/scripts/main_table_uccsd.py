import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from OnePerc_Braiding.Graph_State_Mapping import graph_state_mapping as gsm_oneperc_braiding
from OnePerc.Graph_State_Mapping import graph_state_mapping as gsm_oneperc
from OneMem.Graph_State_Mapping import graph_state_mapping as gsm_onemem
import math



algorithm_type = ['UCCSD']


RefreshBound = 20

oneperc_actual_life_time_list = {}
oneperc_br_actual_life_time_list = {}
onemem_actual_life_time_list = {}
oneperc_refresh_layer_index_list = {}
oneperc_br_refresh_layer_index_list = {}
onemem_refresh_layer_index_list = {}
max_oneperc_measure_delay_list = {}
max_oneperc_br_measure_delay_list = {}
max_onemem_measure_delay_list = {}

for a in ['UCCSD']:
    oneperc_actual_life_time_list[a] = []
    oneperc_br_actual_life_time_list[a] = []
    onemem_actual_life_time_list[a] = []
    oneperc_refresh_layer_index_list[a] = []
    oneperc_br_refresh_layer_index_list[a] = []
    onemem_refresh_layer_index_list[a] = []
    max_oneperc_measure_delay_list[a] = []
    max_oneperc_br_measure_delay_list[a] = []
    max_onemem_measure_delay_list[a] = []
    for N in [24, 26, 60]:
        inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, max_measure_delay = gsm_oneperc_braiding(math.ceil(math.sqrt(N)), N, a, True, RefreshBound)
        oneperc_br_actual_life_time_list[a].append(life_time)
        oneperc_br_refresh_layer_index_list[a].append(layer_index)
        max_oneperc_br_measure_delay_list[a].append(max_measure_delay)
        inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, max_measure_delay = gsm_oneperc(math.ceil(math.sqrt(N)), N, a, True, RefreshBound)
        oneperc_actual_life_time_list[a].append(life_time)
        oneperc_refresh_layer_index_list[a].append(layer_index)
        max_oneperc_measure_delay_list[a].append(max_measure_delay)
        inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, life_time, swap_map = gsm_onemem(math.ceil(math.sqrt(N)), N, a, True, RefreshBound, True, True, 0.4)
        onemem_actual_life_time_list[a].append(life_time)
        onemem_refresh_layer_index_list[a].append(layer_index)
        max_onemem_measure_delay_list[a].append(0)

with open("data/main_table_uccsd.txt", 'w') as file:
    file.write(str(oneperc_actual_life_time_list) + '\n')
    file.write(str(oneperc_br_actual_life_time_list) + '\n')
    file.write(str(onemem_actual_life_time_list) + '\n')
    file.write(str(oneperc_refresh_layer_index_list) + '\n')
    file.write(str(oneperc_br_refresh_layer_index_list) + '\n')
    file.write(str(onemem_refresh_layer_index_list) + '\n')
    file.write(str(max_oneperc_measure_delay_list) + '\n')
    file.write(str(max_oneperc_br_measure_delay_list) + '\n')
    file.write(str(max_onemem_measure_delay_list) + '\n')