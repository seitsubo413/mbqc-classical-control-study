import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import matplotlib.pyplot as plt
import numpy as np
import random
from Build_Cluster.Build_Cluster import *

Row = 6
Depth = 1000
P = 0.75
Overall_Ratio = 1
AverageL = 24
Braiding_Ratio_List = [0.1, 0.2, 0.3, 0.4]
inter_list = [2, 3, 6, 7]

time_index_map = {}
max_inter_space = {}
RunAgain = False
time_index_map['0'] = []
time_index_map['1'] = []
time_index_map['sqrt'] = []
time_index_map['2'] = []
max_inter_space['0'] = []
max_inter_space['1'] = []
max_inter_space['sqrt'] = []
max_inter_space['2'] = []

for Braiding_Ratio in Braiding_Ratio_List:

    swap_map0 = {}
    for d in range(Depth):
        swap_map0[d] = []
        swap_nodes = []
        avail_nodes = []
        for i in range(Row ** 2):
            avail_nodes.append(i)
        while len(swap_nodes) < Overall_Ratio * Row ** 2:
            chosen_pos = avail_nodes[random.randint(0, len(avail_nodes) - 1)]
            swap_map0[d].append((chosen_pos, chosen_pos))
            avail_nodes.remove(chosen_pos)
            swap_nodes.append(chosen_pos)
    time_index_braiding, max_interspace = build_braiding_cluster(Row, Row ** 2, Depth, swap_map0, Row * AverageL, P, AverageL)
    time_index_map['0'].append(time_index_braiding)
    max_inter_space['0'].append(max_interspace)

    swap_map1 = {}
    for d in range(Depth):
        swap_map1[d] = []
        swap_nodes = []
        avail_nodes = []
        direct = [-1, 1, Row, -Row]
        random.shuffle(direct)
        for i in range(Row ** 2):
            avail_nodes.append(i)
        while len(swap_nodes) < 1.5 * Braiding_Ratio * Row ** 2:
            chosen_pos = avail_nodes[random.randint(0, len(avail_nodes) - 1)]
            for dire in direct:
                if (chosen_pos - 1) % Row >= Row - 1 and dire == -1:
                    continue
                if (chosen_pos + 1) % Row <= 0 and dire == 1:
                    continue
                if chosen_pos + dire in avail_nodes:
                    swap_map1[d].append((chosen_pos, chosen_pos + dire))
                    swap_map1[d].append((chosen_pos + dire, chosen_pos))
                    avail_nodes.remove(chosen_pos)
                    avail_nodes.remove(chosen_pos + dire)
                    swap_nodes.append(chosen_pos)        
                    swap_nodes.append(chosen_pos + dire)
                    break
        while len(swap_nodes) < Overall_Ratio * Row ** 2:
            chosen_pos = avail_nodes[random.randint(0, len(avail_nodes) - 1)]
            swap_map1[d].append((chosen_pos, chosen_pos))
            avail_nodes.remove(chosen_pos)
            swap_nodes.append(chosen_pos)
    # print(swap_map1)
    time_index_braiding, max_interspace = build_braiding_cluster(Row, Row ** 2, Depth, swap_map1, Row * AverageL, P, AverageL)
    time_index_map['1'].append(time_index_braiding)
    max_inter_space['1'].append(max_interspace)
    swap_mapsqrt = {}
    for d in range(Depth):
        swap_mapsqrt[d] = []
        swap_nodes = []
        avail_nodes = []
        direct = [-1 + Row, 1 + Row, 1 - Row, -1 - Row]
        random.shuffle(direct)
        for i in range(Row ** 2):
            avail_nodes.append(i)
        while len(swap_nodes) < 1.5 * Braiding_Ratio * Row ** 2:
            chosen_pos = avail_nodes[random.randint(0, len(avail_nodes) - 1)]
            for dire in direct:
                if (chosen_pos - 1) % Row >= Row - 1 and (dire == -1 + Row or dire == -1 - Row):
                    continue
                if (chosen_pos + 1) % Row <= 0 and (dire == 1 + Row or dire == 1 - Row):
                    continue
                if chosen_pos + dire in avail_nodes:
                    swap_mapsqrt[d].append((chosen_pos, chosen_pos + dire))
                    swap_mapsqrt[d].append((chosen_pos + dire, chosen_pos))
                    avail_nodes.remove(chosen_pos)
                    avail_nodes.remove(chosen_pos + dire)
                    swap_nodes.append(chosen_pos)        
                    swap_nodes.append(chosen_pos + dire)
                    break
        while len(swap_nodes) < Overall_Ratio * Row ** 2:
            chosen_pos = avail_nodes[random.randint(0, len(avail_nodes) - 1)]
            swap_mapsqrt[d].append((chosen_pos, chosen_pos))
            avail_nodes.remove(chosen_pos)
            swap_nodes.append(chosen_pos)
    time_index_braiding, max_interspace = build_braiding_cluster(Row, Row ** 2, Depth, swap_mapsqrt, Row * AverageL, P, AverageL)
    time_index_map['sqrt'].append(time_index_braiding)
    max_inter_space['sqrt'].append(max_interspace)
    swap_map2 = {}
    for d in range(Depth):
        swap_map2[d] = []
        swap_nodes = []
        avail_nodes = []
        random.shuffle(direct)
        direct = [-2, 2, 2 * Row, -2 * Row]
        for i in range(Row ** 2):
            avail_nodes.append(i)
        while len(swap_nodes) < 1.5 * Braiding_Ratio * Row ** 2:
            chosen_pos = avail_nodes[random.randint(0, len(avail_nodes) - 1)]
            for dire in direct:
                if (chosen_pos - 2) % Row >= Row - 2 and dire == -2:
                    continue
                if (chosen_pos + 2) % Row <= 1 and dire == 2:
                    continue
                if chosen_pos + dire in avail_nodes:
                    swap_map2[d].append((chosen_pos, chosen_pos + dire))
                    swap_map2[d].append((chosen_pos + dire, chosen_pos))
                    avail_nodes.remove(chosen_pos)
                    avail_nodes.remove(chosen_pos + dire)
                    swap_nodes.append(chosen_pos)        
                    swap_nodes.append(chosen_pos + dire)
                    break
        while len(swap_nodes) < Overall_Ratio * Row ** 2:
            chosen_pos = avail_nodes[random.randint(0, len(avail_nodes) - 1)]
            swap_map2[d].append((chosen_pos, chosen_pos))
            avail_nodes.remove(chosen_pos)
            swap_nodes.append(chosen_pos)
    time_index_braiding, max_interspace = build_braiding_cluster(Row, Row ** 2, Depth, swap_map2, Row * AverageL, P, AverageL)
    time_index_map['2'].append(time_index_braiding)
    max_inter_space['2'].append(max_interspace)

with open("data/ir.txt", 'w') as file:
    file.write(str(time_index_map) + '\n')
    file.write(str(max_inter_space) + '\n')
    file.write(str(inter_list))

