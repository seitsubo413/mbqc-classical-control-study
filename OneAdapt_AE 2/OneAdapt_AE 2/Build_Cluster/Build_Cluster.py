
from Renormalization.Draw_Grid import draw_grid
from Renormalization.Draw_Net import draw_net
from Renormalization.Percolate import *
from Renormalization.Check_Connectivity import *

import networkx as nx


# Execute Braiding Routing
def build_braiding_cluster(Row, NQubit, braiding_depth, swap_gate_depths_qubits, N, P, AverageL):

    cluster_depth = 0
    time_index = 0
    inter_layer_index = 2

    net = nx.Graph()

    #intialized percolation
    net = percolate_intra_layer(net, 0, N, P)

    cluster_info = []
    max_interspace = []
    check_idx = 0
    while cluster_depth < braiding_depth:
        print(cluster_depth)
        net = percolate_intra_layer(net, time_index + 1, N, P)
        net = percolate_inter_layer(net, time_index, N, P)
        if check_idx > 1:
            
            net, i_list, j_list, cross_nodes, flag, i_path_nodes, j_path_nodes, changed_edges = draw_grid(net, time_index, N, AverageL)
            if flag:
                if len(cluster_info) != 0:
                    net, con_flag, changed_edges = check_connectivity_braiding(net, cluster_info, cross_nodes, i_list, j_list, swap_gate_depths_qubits, time_index, i_path_nodes, j_path_nodes, changed_edges, Row, NQubit, N)
                else:
                    con_flag = True
                if con_flag:
                    check_idx = 0
                    if cluster_depth % 20 == 1:
                        refresh_nodes_set = []
                        print(cluster_info[-1][0], time_index)
                        for l in range(max(cluster_info[-1][0] - 3, 0), time_index + 1):
                            for i in range(N):
                                for j in range(N):  
                                    refresh_nodes_set.append(l * N * N + i * N + j)
                        new_net = nx.subgraph(net, refresh_nodes_set).copy() 
                        del net
                        print("del net")
                        net = new_net
                    cluster_info.append((time_index, cross_nodes, i_list, j_list, i_path_nodes, j_path_nodes))
                    cluster_depth += 1
                    max_interspace.append(inter_layer_index + 1)
                    inter_layer_index = 0
                else:
                    check_idx += 1
                    for e in changed_edges.keys():
                        net[e[0]][e[1]]['color'] = changed_edges[e][0]
                        net[e[0]][e[1]]['avail'] = changed_edges[e][1]
                    inter_layer_index += 1
                        # print(net[e[0]][e[1]]['color'], net[e[1]][e[0]]['color'])
                        # print(net[e[0]][e[1]]['avail'], net[e[1]][e[0]]['avail'])
            else:
                check_idx += 1
        else:
            check_idx += 1
            inter_layer_index += 1
        time_index += 1
    return time_index, max_interspace

# Execute Normal Routing
def build_original_cluster(Row, NQubit, original_depth, N, P, AverageL):

    cluster_depth = 0
    time_index = 0
    inter_layer_index = 2

    net = nx.Graph()

    #intialized percolation
    net = percolate_intra_layer(net, 0, N, P)

    cluster_info = []
    while cluster_depth < original_depth:
        print(cluster_depth)
        net = percolate_intra_layer(net, time_index + 1, N, P)
        net = percolate_inter_layer(net, time_index, N, P)
        if inter_layer_index >= 2:
            net, i_list, j_list, cross_nodes, flag, i_path_nodes, j_path_nodes, changed_edges = draw_grid(net, time_index, N, AverageL)
            if flag:
                if len(cluster_info) != 0:
                    net, con_flag, changed_edges = check_connectivity_original(net, cluster_info, cross_nodes, i_list, j_list, time_index, i_path_nodes, j_path_nodes, changed_edges, Row, NQubit, N)
                    con_flag = True
                else:
                    con_flag = True
                if con_flag:
                    cluster_info.append((time_index, cross_nodes, i_list, j_list, i_path_nodes, j_path_nodes))
                    cluster_depth += 1
                    inter_layer_index = 0
                else:
                    for e in changed_edges.keys():
                        net[e[0]][e[1]]['color'] = changed_edges[e][0]
                        net[e[0]][e[1]]['avail'] = changed_edges[e][1]


        else:
            inter_layer_index += 1
        time_index += 1
    return time_index