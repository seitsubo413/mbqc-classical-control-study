import networkx as nx

def find_component(net, time_step, N):
    nodes_list = []
    for i in range(N):
        for j in range(N):
            nodes_list.append(time_step * N * N + i * N + j)

    cur_net = nx.subgraph(net, nodes_list)
    connected_components = list(nx.connected_components(cur_net))
    largest_component = max(connected_components, key=len)

    largest_subgraph = nx.subgraph(cur_net, largest_component).copy()
    return largest_subgraph


def find_root(ptr, x):
    if isinstance(ptr[x], dict):
        return x
    
    ptr[x] = find_root(ptr, ptr[x])
    return ptr[x]

def add_tube(net, snode, changed_edges):
    neigh_snodes = list(net.neighbors(snode))
    avail_neigh_nodes = []
    for neigh_snode in neigh_snodes:
        if net[snode][neigh_snode]['color'] == 'lightgray':
            avail_neigh_nodes.append(neigh_snode)
            nneigh_snodes = list(net.neighbors(neigh_snode))
            if 2 * neigh_snode - snode in nneigh_snodes and net[neigh_snode][2 * neigh_snode - snode]['avail']:
                for nneigh_snode in nneigh_snodes:
                    if nneigh_snode != snode and nneigh_snode != 2 * neigh_snode - snode:
                            if (neigh_snode, nneigh_snode) not in changed_edges.keys() and (nneigh_snode, neigh_snode) not in changed_edges.keys():
                                changed_edges[(neigh_snode, nneigh_snode)] = (net[neigh_snode][nneigh_snode]['color'], net[neigh_snode][nneigh_snode]['avail'])
                                # print(net[neigh_snode][nneigh_snode]['color'], net[neigh_snode][nneigh_snode]['avail'])
                            net[neigh_snode][nneigh_snode]['avail'] = False                
            else:
                for nneigh_snode in nneigh_snodes:
                    if nneigh_snode != snode:
                        if (neigh_snode, nneigh_snode) not in changed_edges.keys() and (nneigh_snode, neigh_snode) not in changed_edges.keys():
                            changed_edges[(neigh_snode, nneigh_snode)] = (net[neigh_snode][nneigh_snode]['color'], net[neigh_snode][nneigh_snode]['avail'])
                            # print(net[neigh_snode][nneigh_snode]['color'], net[neigh_snode][nneigh_snode]['avail'])
                        net[neigh_snode][nneigh_snode]['avail'] = False
    
    # deal with a specific vertical case
    if len(avail_neigh_nodes) == 2:
        if abs(avail_neigh_nodes[0] - snode) !=  abs(avail_neigh_nodes[1] - snode):
            if (avail_neigh_nodes[0],snode) not in changed_edges.keys() and (snode, avail_neigh_nodes[0]) not in changed_edges.keys():
                changed_edges[(avail_neigh_nodes[0],snode)] = (net[avail_neigh_nodes[0]][snode]['color'], net[avail_neigh_nodes[0]][snode]['avail'])
            if (avail_neigh_nodes[1],snode) not in changed_edges.keys() and (snode, avail_neigh_nodes[1]) not in changed_edges.keys():
                changed_edges[(avail_neigh_nodes[1],snode)] = (net[avail_neigh_nodes[1]][snode]['color'], net[avail_neigh_nodes[1]][snode]['avail'])            
            net[avail_neigh_nodes[0]][snode]['avail'] = False    
            net[avail_neigh_nodes[1]][snode]['avail'] = False 
    return net, changed_edges

def find_path_i(net, cur_i, time_step, N, begin_nodes, end_nodes, i_path_nodes, j_path_nodes, cross_nodes, i_index, Lattice_Size, changed_edges):
    node_size = time_step * N * N    
    ptr = {}
    stripe_edges = []
    strip_width = 0
    while cur_i < N:
        # add new i node list to strip
        added_nodes = []
        for j in range(N):
            if node_size + cur_i * N + j in net.nodes():
                an = node_size + cur_i * N + j
                added_nodes.append(an)
                if an in begin_nodes:
                    ptr[an] = {}
                    ptr[an]['begin'] = an
                elif an in end_nodes:
                    ptr[an] = {}
                    ptr[an]['end'] = an
                else:
                    ptr[an] = {}   

        for an in added_nodes:
            if strip_width > 0:
                if an - N in net.nodes() and net.has_edge(an - N, an) and net[an - N][an]['avail']:
                    stripe_edges.append((an - N, an))
                    ran = find_root(ptr, an)
                    ru = find_root(ptr, an - N)
                    if ran != ru:
                        for ran_key in ptr[ran].keys():
                            if ran_key not in ptr[ru].keys():
                                ptr[ru][ran_key] = ptr[ran][ran_key]
                        ptr[ran] = ru
                        if len(list(ptr[ru].keys())) == 2:
                            subgraph = net.edge_subgraph(stripe_edges)
                            shortest_path = nx.shortest_path(subgraph, ptr[ru]['begin'], ptr[ru]['end'])
                            for snode in shortest_path:
                                i_path_nodes[snode] = i_index
                                if snode in j_path_nodes.keys():
                                    if j_path_nodes[snode]  + i_index * Lattice_Size not in cross_nodes.values():
                                        cross_nodes[snode] = j_path_nodes[snode]  + i_index * Lattice_Size
                            pnode = ptr[ru]['begin']
                            for snode in shortest_path[1:]:
                                if (pnode, snode) not in changed_edges.keys() and (snode, pnode) not in changed_edges.keys():
                                    changed_edges[(pnode, snode)] = (net[pnode][snode]['color'], net[pnode][snode]['avail'])
                                    # print(net[pnode][snode]['color'], net[pnode][snode]['avail'])
                                net[pnode][snode]['color'] = 'red'
                                net[pnode][snode]['avail'] = False
                                pnode = snode

                            pnode = ptr[ru]['begin']
                            net, changed_edges = add_tube(net, pnode, changed_edges)
                            for snode in shortest_path[1:]:
                                net, changed_edges = add_tube(net, snode, changed_edges)
                                pnode = snode
                            ptr.clear()
                            stripe_edges.clear()
                            cur_i += 1
                            strip_width = -1
                            break 

            if an % N != N - 1 and an + 1 in net.nodes() and net.has_edge(an, an + 1) and net[an][an + 1]['avail']:
                stripe_edges.append((an, an + 1))
                rran = an + 1
                ran = find_root(ptr, an)
                for rran_key in ptr[rran].keys():
                    if rran_key not in ptr[ran].keys():
                        ptr[ran][rran_key] = ptr[rran][rran_key]      
                ptr[rran] = ran

                if len(list(ptr[ran].keys())) == 2:
                    subgraph = net.edge_subgraph(stripe_edges)
                    shortest_path = nx.shortest_path(subgraph, ptr[ran]['begin'], ptr[ran]['end'])  
                    for snode in shortest_path:
                        i_path_nodes[snode] = i_index
                        if snode in j_path_nodes.keys():
                            if j_path_nodes[snode]  + i_index * Lattice_Size not in cross_nodes.values():
                                cross_nodes[snode] = j_path_nodes[snode]  + i_index * Lattice_Size
                    pnode = ptr[ran]['begin']
                    for snode in shortest_path[1:]:
                        if (pnode, snode) not in changed_edges.keys() and (snode, pnode) not in changed_edges.keys():
                            changed_edges[(pnode, snode)] = (net[pnode][snode]['color'], net[pnode][snode]['avail'])
                            # print(net[pnode][snode]['color'], net[pnode][snode]['avail'])

                        net[pnode][snode]['color'] = 'red'
                        net[pnode][snode]['avail'] = False
                        pnode = snode
                    pnode = ptr[ru]['begin']
                    net, changed_edges = add_tube(net, pnode, changed_edges)
                    for snode in shortest_path[1:]:
                        net, changed_edges = add_tube(net, snode, changed_edges)
                        pnode = snode
                    ptr.clear()
                    stripe_edges.clear()
                    cur_i += 1
                    strip_width = -1
                    break   
        if strip_width == -1:
            return cur_i + 4, net, True, i_path_nodes, cross_nodes, changed_edges
        cur_i += 1
        strip_width += 1
    return cur_i, net, False, i_path_nodes, cross_nodes, changed_edges

def find_path_j(net, cur_j, time_step, N, begin_nodes, end_nodes, i_path_nodes, j_path_nodes, cross_nodes, j_index, Lattice_Size, changed_edges):
    node_size = time_step * N * N

    ptr = {}
    strip_edges = []
    strip_width = 0
    while cur_j < N:
        added_nodes = []
        for i in range(N):
            if node_size + i * N + cur_j in net.nodes():
                an = node_size + i * N + cur_j
                added_nodes.append(an)
                if an in begin_nodes:
                    ptr[an] = {}
                    ptr[an]['begin'] = an
                elif an in end_nodes:
                    ptr[an] = {}
                    ptr[an]['end'] = an
                else:
                    ptr[an] = {}    
           
        for an in added_nodes:
            if strip_width > 0:
                if an - 1 in net.nodes() and net.has_edge(an - 1, an) and net[an - 1][an]['avail']:
                    strip_edges.append((an - 1, an))
                    ran = find_root(ptr, an)
                    rl = find_root(ptr, an - 1)
                    if ran != rl:
                        for ran_key in ptr[ran].keys():
                            if ran_key not in ptr[rl].keys():
                                ptr[rl][ran_key] = ptr[ran][ran_key]
                        ptr[ran] = rl
                        if len(list(ptr[rl].keys())) == 2:
                            subgraph = net.edge_subgraph(strip_edges)
                            shortest_path = nx.shortest_path(subgraph, ptr[rl]['begin'], ptr[rl]['end'])
                            for snode in shortest_path:
                                j_path_nodes[snode] = j_index
                                if snode in i_path_nodes.keys():
                                    if i_path_nodes[snode] * Lattice_Size  + j_index not in cross_nodes.values():
                                        cross_nodes[snode] = i_path_nodes[snode] * Lattice_Size  + j_index

                            pnode = ptr[rl]['begin']
                            for snode in shortest_path[1:]:
                                if (pnode, snode) not in changed_edges.keys() and (snode, pnode) not in changed_edges.keys():
                                    changed_edges[(pnode, snode)] = (net[pnode][snode]['color'], net[pnode][snode]['avail'])
                                    # print(net[pnode][snode]['color'], net[pnode][snode]['avail'])
                                net[pnode][snode]['color'] = 'red'
                                net[pnode][snode]['avail'] = False
                                pnode = snode
                            pnode = ptr[rl]['begin']
                            net, changed_edges = add_tube(net, pnode, changed_edges)
                            for snode in shortest_path[1:]:
                                net, changed_edges = add_tube(net, snode, changed_edges)
                            pnode = snode
                            ptr.clear()
                            strip_edges.clear()
                            cur_j += 1
                            strip_width = -1
                            break
            if an + N in net.nodes() and net.has_edge(an, an + N) and net[an][an + N]['avail']:
                strip_edges.append((an, an + N))
                dan = an + N
                ran = find_root(ptr, an)
                for dan_key in ptr[dan].keys():
                    if dan_key not in ptr[ran].keys():
                        ptr[ran][dan_key] = ptr[dan][dan_key]      
                ptr[dan] = ran

                if len(list(ptr[ran].keys())) == 2:
                    subgraph = net.edge_subgraph(strip_edges)
                    shortest_path = nx.shortest_path(subgraph, ptr[ran]['begin'], ptr[ran]['end'])
                    for snode in shortest_path:
                        j_path_nodes[snode] = j_index
                        if snode in i_path_nodes.keys():
                            if i_path_nodes[snode] * Lattice_Size  + j_index not in cross_nodes.values():
                                cross_nodes[snode] = i_path_nodes[snode] * Lattice_Size  + j_index
                    pnode = ptr[ran]['begin']
                    for snode in shortest_path[1:]:
                        if (pnode, snode) not in changed_edges.keys() and (snode, pnode) not in changed_edges.keys():
                            changed_edges[(pnode, snode)] = (net[pnode][snode]['color'], net[pnode][snode]['avail'])
                            # print(net[pnode][snode]['color'], net[pnode][snode]['avail'])
                        net[pnode][snode]['color'] = 'red'
                        net[pnode][snode]['avail'] = False
                        pnode = snode
                    pnode = ptr[rl]['begin']
                    net, changed_edges = add_tube(net, pnode, changed_edges)
                    for snode in shortest_path[1:]:
                        net, changed_edges = add_tube(net, snode, changed_edges)
                    pnode = snode
                    ptr.clear()
                    strip_edges.clear()
                    cur_j += 1
                    strip_width = -1
                    break 
        if strip_width == -1:
            return cur_j + 3, net, True, j_path_nodes, cross_nodes, changed_edges
        cur_j += 1
        strip_width += 1
    return cur_j, net, False, j_path_nodes, cross_nodes, changed_edges

def draw_grid(net, time_step, N, Average_L):
    i_path_nodes = {}
    j_path_nodes = {}
    cross_nodes = {}

    cur_i = 3
    cur_j = 3

    i_index = 0
    j_index = 0 
    
    i_list = [1]
    j_list = [1]
    
    begin_nodes_i = []
    end_nodes_i = []
    begin_nodes_j = []
    end_nodes_j = []

    changed_edges = {}
    # print("draw_grid")
    # determine begin nodes and end nodes
    new_net = find_component(net, time_step, N)
    node_size = time_step * N * N
    for i in range(N):
        for j in range(N):
            if node_size + i * N + j in new_net.nodes():
                begin_nodes_i.append(node_size + i * N + j)
                break
    
    for i in range(N):
        for j in range(N):
            if node_size + i * N + N - 1 - j in new_net.nodes():
                end_nodes_i.append(node_size + i * N + N - 1 - j)
                break
            
    for i in range(N):
        for j in range(N):
            if node_size + j * N + i in net.nodes():
                begin_nodes_j.append(node_size + j * N + i)
                break

    for i in range(N):
        for j in range(N):
            if node_size + (N - 1 - j) * N + i in net.nodes():
                end_nodes_j.append(node_size + (N - 1 - j) * N + i)
                break

    while cur_i < N and cur_j < N:
        if cur_i < N and i_index < N // Average_L:
            cur_i, net, find_flag, i_path_nodes, cross_nodes, changed_edges = find_path_i(net, cur_i, time_step, N, begin_nodes_i, end_nodes_i, i_path_nodes, j_path_nodes, cross_nodes, i_index, N // Average_L, changed_edges)
            if find_flag:
                if cur_i < N:
                    i_list.append(cur_i - 1)
                else:
                    i_list.append(N - 1)
                i_index += 1
                
        if cur_j < N and j_index < N // Average_L:
            cur_j, net, find_flag, j_path_nodes, cross_nodes, changed_edges = find_path_j(net, cur_j, time_step, N, begin_nodes_j, end_nodes_j, i_path_nodes, j_path_nodes, cross_nodes, j_index, N // Average_L, changed_edges)
            if find_flag:
                if cur_j < N:
                    j_list.append(cur_j - 1)
                else:
                    j_list.append(N - 1)
                j_index += 1
        if i_index >= N // Average_L and j_index >= N // Average_L:
                    break
        
    if len(list(cross_nodes.keys())) !=  (N // Average_L) ** 2 or i_index !=  N // Average_L:
        # print(len(list(cross_nodes.keys())))
        for e in changed_edges.keys():
            net[e[0]][e[1]]['color'] = changed_edges[e][0]
            net[e[0]][e[1]]['avail'] = changed_edges[e][1]
            # print(net[e[0]][e[1]]['color'], net[e[1]][e[0]]['color'])
            # print(net[e[0]][e[1]]['avail'], net[e[1]][e[0]]['avail'])
        return net, i_list, j_list, cross_nodes, False, {}, {}, {}
    else:
        return net, i_list, j_list, cross_nodes, True, i_path_nodes, j_path_nodes, changed_edges
        
