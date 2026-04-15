# last q0 to q1
import networkx as nx
def add_tube(net, snode, changed_edges):
    neigh_snodes = list(net.neighbors(snode))
    avail_neigh_nodes = []
    for neigh_snode in neigh_snodes:
        if net[snode][neigh_snode]['color'] == 'lightgray':
            avail_neigh_nodes.append(neigh_snode)
            nneigh_snodes = list(net.neighbors(neigh_snode))
            if 2 * neigh_snode - snode in nneigh_snodes and net[neigh_snode][2 * neigh_snode - snode]['avail']:
                for nneigh_snode in nneigh_snodes:
                    if nneigh_snode != 2 * neigh_snode - snode:
                            if (neigh_snode, nneigh_snode) not in changed_edges.keys() and (nneigh_snode, neigh_snode) not in changed_edges.keys():
                                changed_edges[(neigh_snode, nneigh_snode)] = (net[neigh_snode][nneigh_snode]['color'], net[neigh_snode][nneigh_snode]['avail'])
                                # print(net[neigh_snode][nneigh_snode]['color'], net[neigh_snode][nneigh_snode]['avail'])
                            # else:
                            #     print("correct response")
                            net[neigh_snode][nneigh_snode]['avail'] = False                
            else:
                for nneigh_snode in nneigh_snodes:
                    if (neigh_snode, nneigh_snode) not in changed_edges.keys() and (nneigh_snode, neigh_snode) not in changed_edges.keys():
                        changed_edges[(neigh_snode, nneigh_snode)] = (net[neigh_snode][nneigh_snode]['color'], net[neigh_snode][nneigh_snode]['avail'])
                        # print(net[neigh_snode][nneigh_snode]['color'], net[neigh_snode][nneigh_snode]['avail'])
                    # else:
                    #     print("correct response")
                    net[neigh_snode][nneigh_snode]['avail'] = False
    
    return net, changed_edges

def check_last_q0_q1(net, cluster_info, cross_nodes, q0, q1, i_list, j_list, i_path_nodes, j_path_nodes, time_index, Lattice_Size, N, changed_edges):
    last_q0_pos = next((k for k, v in cluster_info[-1][1].items() if v == q0), None)
    q1_pos = next((k for k, v in cross_nodes.items() if v == q1), None)
    q0_i = q0 // Lattice_Size
    q0_j = q0 % Lattice_Size
    q1_i = q1 // Lattice_Size
    q1_j = q1 % Lattice_Size
    last_i_list = cluster_info[-1][2]
    last_j_list = cluster_info[-1][3]

    last_i_path_nodes = cluster_info[-1][4]
    last_j_path_nodes = cluster_info[-1][5]

    last_node_size = cluster_info[-1][0] * N * N
    cur_node_size = time_index * N * N

    last_routing_nodes = [(last_q0_pos, [last_q0_pos])]
    cross_five_nodes = [last_q0_pos]
    neigh_q0_nodes = net.neighbors(last_q0_pos)
    for neigh_q0_node in neigh_q0_nodes:
        cross_five_nodes.append(neigh_q0_node)
    
    i_nodes = []
    for i in range(last_i_list[q0_i], last_i_list[q0_i + 1]):
        for j in range(last_j_list[q0_j], last_j_list[q0_j + 1]):
            if i * N + j + last_node_size not in cross_five_nodes and i * N + j + last_node_size not in last_j_path_nodes.keys():
                i_nodes.append(i * N + j + last_node_size)
    i_net = nx.subgraph(net, i_nodes)
    connected_components = list(nx.connected_components(i_net))
    for component in connected_components:
        for cnode in component:
            if cnode in last_i_path_nodes.keys():
                last_routing_nodes.append((cnode, list(component)))
                break

    j_nodes = []
    for i in range(last_i_list[q0_i], last_i_list[q0_i + 1]):
        for j in range(last_j_list[q0_j], last_j_list[q0_j + 1]):
            if i * N + j + last_node_size not in cross_five_nodes and i * N + j + last_node_size not in last_i_path_nodes.keys():
                j_nodes.append(i * N + j + last_node_size)
    j_net = nx.subgraph(net, j_nodes)
    connected_components = list(nx.connected_components(j_net))
    for component in connected_components:
        for cnode in component:
            if cnode in last_j_path_nodes.keys():
                last_routing_nodes.append((cnode, list(component)))
                break

    #####
    cur_routing_nodes = [(q1_pos, [q1_pos])]
    cross_five_nodes = [q1_pos]
    neigh_q1_nodes = net.neighbors(q1_pos)
    for neigh_q1_node in neigh_q1_nodes:
        cross_five_nodes.append(neigh_q1_node)
    
    i_nodes = []
    for i in range(i_list[q1_i], i_list[q1_i + 1]):
        for j in range(j_list[q1_j], j_list[q1_j + 1]):
            if i * N + j + cur_node_size not in cross_five_nodes and i * N + j + cur_node_size not in j_path_nodes.keys():
                i_nodes.append(i * N + j + cur_node_size)
    i_net = nx.subgraph(net, i_nodes)
    connected_components = list(nx.connected_components(i_net))
    for component in connected_components:
        for cnode in component:
            if cnode in i_path_nodes.keys():
                cur_routing_nodes.append((cnode, list(component)))
                break

    j_nodes = []
    for i in range(i_list[q1_i], i_list[q1_i + 1]):
        for j in range(j_list[q1_j], j_list[q1_j + 1]):
            if i * N + j + cur_node_size not in cross_five_nodes and i * N + j + cur_node_size not in i_path_nodes.keys():
                j_nodes.append(i * N + j + cur_node_size)
    j_net = nx.subgraph(net, j_nodes)
    connected_components = list(nx.connected_components(j_net))
    for component in connected_components:
        for cnode in component:
            if cnode in j_path_nodes.keys():
                last_routing_nodes.append((cnode, list(component)))
                break
    ########
    routing_edges_basic = []
    for t in range(cluster_info[-1][0] + 1, time_index):
        for i in range(N):
            for j in range(N):
                if i > 0:
                    if net.has_edge(t * N * N + i * N + j, t * N * N + (i - 1) * N + j) and net[t * N * N + i * N + j][t * N * N + (i - 1) * N + j]['avail']:
                        routing_edges_basic.append((t * N * N + i * N + j, t * N * N + (i - 1) * N + j))
                if j > 0:
                    if net.has_edge(t * N * N + i * N + j, t * N * N + i * N + j - 1) and net[t * N * N + i * N + j][t * N * N + i * N + j - 1]['avail']:
                        routing_edges_basic.append((t * N * N + i * N + j, t * N * N + i * N + j - 1))
        if t != time_index - 1:
            for i in range(N):
                for j in range(N):
                    if net.has_edge(i * N + j + t * N * N, i * N + j + (t + 1) * N * N) and net[i * N + j + t * N * N][i * N + j + (t + 1) * N * N]['avail']:
                        routing_edges_basic.append((i * N + j + t * N * N, i * N + j + (t + 1) * N * N))               

    for last_routing_node_set in last_routing_nodes:
        for cur_routing_node_set in cur_routing_nodes:
            routing_edges = []
            last_edges = nx.subgraph(net, last_routing_node_set[1]).edges()
            # print(last_routing_node_set[1])
            for e in last_edges:
                if net[e[0]][e[1]]['avail'] or net[e[0]][e[1]]['color'] == 'red':
                    routing_edges.append(e)
            for n in last_routing_node_set[1]:
                if net.has_edge(n + N * N, n) and net[n + N * N][n]['avail']:
                    routing_edges.append((n + N * N, n))

            cur_edges = nx.subgraph(net, cur_routing_node_set[1]).edges()
            for e in cur_edges:
                if net[e[0]][e[1]]['avail'] or net[e[0]][e[1]]['color'] == 'red':
                    routing_edges.append(e)
            for n in cur_routing_node_set[1]:
                if net.has_edge(n - N * N, n) and net[n - N * N][n]['avail']:
                    routing_edges.append((n - N * N, n))
            
            routing_edges += routing_edges_basic
            routing_subgraph =  net.edge_subgraph(routing_edges)
            if last_routing_node_set[0] in routing_subgraph.nodes() and cur_routing_node_set[0] in routing_subgraph.nodes() and nx.has_path(routing_subgraph, last_routing_node_set[0], cur_routing_node_set[0]):
                shortest_path = nx.shortest_path(routing_subgraph, last_routing_node_set[0], cur_routing_node_set[0])
                pnode = last_routing_node_set[0]
                for snode in shortest_path[1:]:
                    if (pnode, snode) not in changed_edges.keys() and (snode, pnode) not in changed_edges.keys():
                        changed_edges[(pnode, snode)] = (net[pnode][snode]['color'], net[pnode][snode]['avail'])
                        # print(net[pnode][snode]['color'], net[pnode][snode]['avail'])
                    # else:
                    #     print("correct response")
                    net[pnode][snode]['color'] = 'red'
                    net[pnode][snode]['avail'] = False
                    pnode = snode
                pnode = last_routing_node_set[0]
                net, changed_edges = add_tube(net, pnode, changed_edges)
                for snode in shortest_path[1:]:
                    net, changed_edges = add_tube(net, snode, changed_edges)
                    pnode = snode
                return net, True, changed_edges

    return net, False, changed_edges

def check_connectivity_braiding(net, cluster_info, cross_nodes, i_list, j_list, swap_gate_depths_qubits, time_index, i_path_nodes, j_path_nodes, changed_edges, Lattice_Size, NQubit, N):
    all_qubits = []
    for i in range(NQubit):
        all_qubits.append(i)


    if len(cluster_info) - 1 in swap_gate_depths_qubits.keys():
        for swap_qubits_pair in swap_gate_depths_qubits[len(cluster_info) - 1]:
            q0 = swap_qubits_pair[0]
            q1 = swap_qubits_pair[1]
            print(q0, q1)
            net, single_con_flag, changed_edges = check_last_q0_q1(net, cluster_info, cross_nodes, q0, q1, i_list, j_list, i_path_nodes, j_path_nodes, time_index, Lattice_Size, N, changed_edges)
            if not single_con_flag:
                return net, False, changed_edges
            
            # net, single_con_flag, changed_edges = check_last_q0_q1(net, cluster_info, cross_nodes, q1, q0, i_list, j_list, i_path_nodes, j_path_nodes, time_index, Lattice_Size, N, changed_edges)
            # if not single_con_flag:
            #     return net, False, changed_edges
            
            # all_qubits.remove(q0)
            # all_qubits.remove(q1)
    
    # for q in all_qubits:
    #     net, single_con_flag, changed_edges = check_last_q0_q1(net, cluster_info, cross_nodes, q, q, i_list, j_list, i_path_nodes, j_path_nodes, time_index, Lattice_Size, N, changed_edges)
    #     if not single_con_flag:
    #         # print("False")
    #         return net, False, changed_edges       
            
    # print("True")
    return net, True, changed_edges

def check_connectivity_original(net, cluster_info, cross_nodes, i_list, j_list, time_index, i_path_nodes, j_path_nodes, changed_edges, Lattice_Size, NQubit, N):
    all_qubits = []
    for i in range(NQubit):
        all_qubits.append(i)

    for q in all_qubits:
        net, single_con_flag, changed_edges = check_last_q0_q1(net, cluster_info, cross_nodes, q, q, i_list, j_list, i_path_nodes, j_path_nodes, time_index, Lattice_Size, N, changed_edges)
        if not single_con_flag:
            # print("False")
            return net, False, changed_edges       
            
    # print("True")
    return net, True, changed_edges