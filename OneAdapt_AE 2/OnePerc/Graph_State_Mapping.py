import networkx as nx
import matplotlib.pyplot as plt
import os

from OnePerc.Construct_Test_Circuit import *
from OnePerc.Graph_State import *
from OnePerc.Mapping_Routing_origin import *
from OnePerc.Reduce_Degree import *
from OnePerc.Determine_Dependency import *


def empty_folder(folder_path):
    if os.path.exists(folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                empty_folder(item_path)
        print(f"Folder '{folder_path}' has been emptied.")
    else:
        print(f"Folder '{folder_path}' does not exist.")

def graph_state_mapping(N_size, NQubit, algorithm_type, Refresh, RefreshBound):
    empty_folder("layers/")
    
    # construct circuit
    if algorithm_type == 'QAOA':
        gates_list, qubits = construct_qaoa(NQubit, 0.5)
    elif algorithm_type == 'QFT':
        gates_list, qubits = construct_qft(NQubit)
    elif algorithm_type == 'RCA':
        gates_list, qubits = construct_rca(NQubit)
    elif algorithm_type == 'VQE':
        gates_list, qubits = construct_vqe(NQubit)
    elif algorithm_type == 'BV':
        gates_list, qubits = construct_bv(NQubit)
    elif algorithm_type == 'QSIM':
        gates_list, qubits = construct_qsim(NQubit)
    elif algorithm_type == 'Grover':
        gates_list, qubits = construct_grover(NQubit)
    elif algorithm_type == 'UCCSD':
        gates_list, qubits = construct_uccsd(NQubit)

    # convert circuit to graph state
    gs = generate_graph_state(gates_list, qubits)

    # determine dependency
    dgraph, gs = determine_dependency(gs)

    # transform gs to undirected since dependency has been analyzed    
    undirected_gs = nx.Graph(gs)

    # reduce degree for undirected_gs to accelerate mapping and routing
    lgs = reduce_degree(undirected_gs)

    # map & route
    net_list, layer_index, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay = map_route(lgs, dgraph, NQubit, N_size, Refresh, RefreshBound)
    
    print("layer_index", layer_index)
    
    # plot the graph nodes descending curve
    # plt.plot(layer_list, left_graph_nodes_list, color='black', marker='o', linestyle='-', linewidth=2, markersize=2)

    # plt.legend()
    # plt.title('map & route')
    # plt.xlabel('layer number')
    # plt.ylabel('left graph nodes') 
    return inter_edges_list, layer_index, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay
