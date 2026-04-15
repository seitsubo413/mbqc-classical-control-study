import networkx as nx
import matplotlib.pyplot as plt
import random
import math
import heapq

Empty = 1e1000
Auxiliary = -1
SearchUpperBound = 40
Average_Depth = 1
Round = 4

def count_pos_untake(net, pos, N):
    pos_i = pos // N
    pos_j = pos % N
    untake_node_list = []
    if pos_i > 0:
        if net.nodes[(pos_i - 1) * N + pos_j]['node_val'] == Empty:
            untake_node_list.append((pos_i - 1) * N + pos_j)
    if pos_j > 0:
        if net.nodes[pos_i * N + pos_j - 1]['node_val'] == Empty:
            untake_node_list.append(pos_i * N + pos_j - 1)      

    if pos_i < N - 1:
        if net.nodes[(pos_i + 1) * N + pos_j]['node_val'] == Empty:
            untake_node_list.append((pos_i + 1) * N + pos_j)   
    
    if pos_j < N - 1:
        if net.nodes[pos_i * N + pos_j + 1]['node_val'] == Empty:
            untake_node_list.append(pos_i * N + pos_j + 1) 
    return untake_node_list

def lead_to_blockness(net, allocated_incomplete_nodes, untake_pos, N):
    up_pos = untake_pos - N
    down_pos = untake_pos + N
    left_pos = untake_pos - 1
    right_pos = untake_pos + 1

    if up_pos >= 0 and net.nodes[up_pos]['node_val'] != Empty and len(count_pos_untake(net, up_pos, N))  <= 1 and up_pos in allocated_incomplete_nodes:
        return True

    if down_pos <= N * N - 1 and net.nodes[down_pos]['node_val'] != Empty and len(count_pos_untake(net, down_pos, N))  <= 1 and down_pos in allocated_incomplete_nodes:
        return True

    if left_pos % N != N - 1 and net.nodes[left_pos]['node_val'] != Empty and len(count_pos_untake(net, left_pos, N))  <= 1 and left_pos in allocated_incomplete_nodes:
        return True

    if right_pos % N != 0 and net.nodes[right_pos]['node_val'] != Empty and len(count_pos_untake(net, right_pos, N))  <= 1 and right_pos in allocated_incomplete_nodes:
        return True  
    return False

def be_blocked(net, pos, N):
    free_space = 0
    up_pos = pos - N
    down_pos = pos + N
    left_pos = pos - 1
    right_pos = pos + 1

    if up_pos >= 0 and net.nodes[up_pos]['node_val'] == Empty:
        free_space += 1

    if down_pos <= N * N - 1 and net.nodes[down_pos]['node_val'] == Empty:
        free_space += 1

    if left_pos % N != N - 1 and net.nodes[left_pos]['node_val'] == Empty:
        free_space += 1

    if right_pos % N != 0 and net.nodes[right_pos]['node_val'] == Empty:
        free_space += 1
  
    return free_space < 2

def is_isolated(net, pos, N):
    flag = True
    up_pos = pos - N
    down_pos = pos + N
    left_pos = pos - 1
    right_pos = pos + 1

    if up_pos >= 0 and net[pos][up_pos]['color'] == 'red':
        flag = False

    if down_pos <= N * N - 1 and net[pos][down_pos]['color'] == 'red':
        flag = False

    if left_pos % N != N - 1 and net[pos][left_pos]['color'] == 'red':
        flag = False

    if right_pos % N != 0 and net[pos][right_pos]['color'] == 'red':
        flag = False   
    return flag

class SearchNode:
    def __init__(self, net, path, allocated_incomplete_nodes, N):
        self.net = net.copy()
        self.path = path.copy()
        self.f = 0
        self.free_space = set()
        for pnode in path:
            for nnode in count_pos_untake(net, pnode, N):
                # if not lead_to_blockness(net, allocated_incomplete_nodes, nnode) and not be_blocked(net, nnode):
                self.free_space.add(nnode)
        self.f = len(self.free_space)
    def __lt__(self, other):
        return self.f > other.f  

def find_pre_pos(path, pos, N):
    pos_i = pos // N
    pos_j = pos % N
    
    if pos_i > 0:
        if (pos_i - 1) * N + pos_j in path:
            return (pos_i - 1) * N + pos_j
    
    if pos_j > 0:
        if pos_i * N + pos_j - 1 in path:
            return pos_i * N + pos_j - 1
    
    if pos_i < N - 1:
        if (pos_i + 1) * N + pos_j in path:
            return (pos_i + 1) * N + pos_j   

    if pos_j < N - 1:
        if pos_i * N + pos_j + 1 in path:
            return pos_i * N + pos_j + 1  
    return -1

def create_net(allocated_incomplete_nodes, N):
    net = nx.Graph()
    for i in range(N):
        for j in range(N):
            if i * N + j not in allocated_incomplete_nodes.keys():
                net.add_node(i * N + j, pos = (j, i), node_val = Empty, node_color = 'lightgray')
            else:
                net.add_node(i * N + j, pos = (j, i), node_val = allocated_incomplete_nodes[i * N + j], node_color = 'black')

    for i in range(N):
        for j in range(N):
            if i < N - 1:
                net.add_edge(i * N + j, (i + 1) * N + j, color = 'lightgray')
            if j > 0:
                net.add_edge(i * N + j, i * N + j - 1, color = 'lightgray')
    return net

def draw_net(net):
    pos = nx.get_node_attributes(net, 'pos')
    nx.draw(net, pos, node_size = 3)
    return

def save_net(net, layer_index, N):
    plt.figure(figsize=(N, N))

    pos = nx.get_node_attributes(net, 'pos')

    for u, v, data in net.edges(data=True):
            nx.draw_networkx_edges(net, pos, edgelist=[(u, v)], edge_color=net[u][v]['color'], alpha=0.7)
    
    node_colors = [net.nodes[n]['node_color'] for n in net.nodes()]
    nx.draw_networkx_nodes(net, pos = pos, node_size = 5, node_color = node_colors)
    plt.savefig("layers/layer" + str(layer_index) + ".png")
    return

def dfs_path(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if start not in graph:
        return False
    neigh_nodes = list(graph.neighbors(start))
    random.shuffle(neigh_nodes)
    for neighbor in neigh_nodes:
        if neighbor not in path:
            new_path = dfs_path(graph, neighbor, end, path)
            if new_path:
                return new_path
    return False

def change_pos(pos, pos_map, N):
    if pos not in pos_map.keys():
        return True, 0
    else:
        if pos % N > 0 and pos - 1 not in pos_map.keys():
            return True, -1
        elif pos % N < N - 1 and pos + 1 not in pos_map.keys():
            return True, 1
        elif pos // N > 0 and pos - N not in pos_map.keys():
            return True, - N
        elif pos // N < N - 1 and pos + N not in pos_map.keys():
            return True, N
        else:
            return False, 0

def one_layer_map_route(origin_graph, dgraph, allocated_nodes_cache, graph_nodes_pos, layer_index, N, required_life_time, Refresh, RefreshBound, NQubit, P, D_Flag, Braiding, nodes_to_be_measured, layer_graph_map, MixedBound, nodes_to_appear):
    layer_graph_map[layer_index] = (origin_graph.copy(), dgraph.copy(), nodes_to_be_measured.copy(), allocated_nodes_cache.copy(), graph_nodes_pos.copy(), P, nodes_to_appear.copy())
    all_qubits_to_be_mapped = []
    for q in range(NQubit):
        all_qubits_to_be_mapped.append(q)
    
    pre_layer_incomplete_nodes = {}

    print("cache size,", len(list(allocated_nodes_cache.keys())))

    # get refresh nodes
    refresh_nodes = []
    index = 0
    if Refresh:     
        for gnode in graph_nodes_pos.keys():
            if layer_index - graph_nodes_pos[gnode] >= RefreshBound and gnode not in refresh_nodes and gnode in allocated_nodes_cache.keys():
                if allocated_nodes_cache[gnode] not in pre_layer_incomplete_nodes.keys():
                    refresh_nodes.append(gnode)       
                    pre_layer_incomplete_nodes[allocated_nodes_cache[gnode]] = gnode
                    del allocated_nodes_cache[gnode]
                    index += 1
                else:
                    if graph_nodes_pos[pre_layer_incomplete_nodes[allocated_nodes_cache[gnode]]] > graph_nodes_pos[gnode]:
                        refresh_nodes.remove(pre_layer_incomplete_nodes[allocated_nodes_cache[gnode]])
                        refresh_nodes.append(gnode)
                        allocated_nodes_cache[pre_layer_incomplete_nodes[allocated_nodes_cache[gnode]]] = allocated_nodes_cache[gnode]
                        pre_layer_incomplete_nodes[allocated_nodes_cache[gnode]] = gnode
                        del allocated_nodes_cache[gnode]

        for rnode in refresh_nodes:
            if origin_graph.nodes[rnode]['qubit'] in all_qubits_to_be_mapped:
                all_qubits_to_be_mapped.remove(origin_graph.nodes[rnode]['qubit'])

    if len(list(allocated_nodes_cache.keys())):
        print(len(list(pre_layer_incomplete_nodes.values())) / len(list(allocated_nodes_cache.keys())))

    cur_force_refresh_nodes_num = len(list(pre_layer_incomplete_nodes.values()))
    print('refresh size', len(list(pre_layer_incomplete_nodes.values())))
    reverse_map_origin = allocated_nodes_cache.copy()
    swap_nodes = []
    swap_pairs = []
    items = graph_nodes_pos.items()

    sorted_items = sorted(items, key=lambda x: x[1])

    sorted_graph_nodes_pos = {k: v for k, v in sorted_items}   

    for kr in range(2):
        keys = list(sorted_graph_nodes_pos.keys()).copy()
        while(keys):
            if index >= N * N * P:
                break
            key = keys[0]
            keys.remove(key)
            if key in allocated_nodes_cache.keys():           
                flag = False
                akeys = list(allocated_nodes_cache.keys()).copy()
                
                for kkey in pre_layer_incomplete_nodes.values():
                    if origin_graph.has_edge(key, kkey):
                        flag = True
                        break
                if flag:
                    if allocated_nodes_cache[key] not in pre_layer_incomplete_nodes.keys():
                        pre_layer_incomplete_nodes[allocated_nodes_cache[key]] = key
                        del allocated_nodes_cache[key]
                        index += 1
                    elif Braiding:
                        direct = []
                        x = allocated_nodes_cache[key] // N
                        y = allocated_nodes_cache[key] % N
                        if x > 0:
                            direct.append(-N)
                        if x < N - 1:
                            direct.append(N)
                        if y > 0:
                            direct.append(-1)
                        if y < N - 1:
                            direct.append(1)
                        for d in direct:
                            if allocated_nodes_cache[key] + d not in pre_layer_incomplete_nodes.keys():
                                pre_layer_incomplete_nodes[allocated_nodes_cache[key] + d] = key
                                swap_nodes.append(key)
                                swap_pairs.append((allocated_nodes_cache[key], allocated_nodes_cache[key] + d))
                                del allocated_nodes_cache[key]
                                index += 1
                                break

    keys = list(sorted_graph_nodes_pos.keys()).copy()
    while(keys):
        if index >= N * N * P:
            break
        key = keys[0]
        keys.remove(key)
        if key in allocated_nodes_cache.keys():
            if allocated_nodes_cache[key] not in pre_layer_incomplete_nodes.keys():
                flag = False
                akeys = list(allocated_nodes_cache.keys()).copy()
                for kkey in akeys:
                    if origin_graph.has_edge(key, kkey) and allocated_nodes_cache[kkey] not in pre_layer_incomplete_nodes.keys():
                        if allocated_nodes_cache[kkey] != allocated_nodes_cache[key]:
                            pre_layer_incomplete_nodes[allocated_nodes_cache[kkey]] = kkey
                            del allocated_nodes_cache[kkey]  
                            index += 1 
                            flag = True
                        elif Braiding:
                            direct = []
                            x = allocated_nodes_cache[kkey] // N
                            y = allocated_nodes_cache[kkey] % N
                            if x > 0:
                                direct.append(-N)
                            if x < N - 1:
                                direct.append(N)
                            if y > 0:
                                direct.append(-1)
                            if y < N - 1:
                                direct.append(1)
                            for d in direct:
                                if allocated_nodes_cache[kkey] + d not in pre_layer_incomplete_nodes.keys():
                                    pre_layer_incomplete_nodes[allocated_nodes_cache[kkey] + d] = kkey
                                    swap_nodes.append(kkey)
                                    swap_pairs.append((allocated_nodes_cache[kkey], allocated_nodes_cache[kkey] + d))
                                    del allocated_nodes_cache[kkey]
                                    index += 1
                                    break
                if flag:
                    pre_layer_incomplete_nodes[allocated_nodes_cache[key]] = key
                    del allocated_nodes_cache[key]
                    index += 1
   


    keys = list(sorted_graph_nodes_pos.keys()).copy()
    while(keys):
        if index >= N * N * P:
            break
        key = keys[0]
        keys.remove(key)

        if key in allocated_nodes_cache.keys():
            if allocated_nodes_cache[key] not in pre_layer_incomplete_nodes.keys():
                flag = True 
                for nkey in origin_graph.neighbors(key):
                    if nkey in pre_layer_incomplete_nodes.values() or nkey in allocated_nodes_cache.keys():
                        flag = False
                        break
                if flag:
                    pre_layer_incomplete_nodes[allocated_nodes_cache[key]] = key
                    del allocated_nodes_cache[key]
                    index += 1

    print("all refresh nodes", len(pre_layer_incomplete_nodes))
    # sabre swap
    reverse_map = {}
    for key in pre_layer_incomplete_nodes.keys():
        reverse_map[pre_layer_incomplete_nodes[key]] = key
    if Braiding:       
        degree_map = {}
        for key in reverse_map.keys():
            degree_map[key] = []
            neigh_knodes = origin_graph.neighbors(key)
            for nknode in neigh_knodes:
                if nknode in reverse_map.keys():
                    degree_map[key].append(nknode)

        items = degree_map.items()

        sorted_items = sorted(items, key=lambda x: len(x[1]), reverse=True)

        sorted_degree_map = {k: v for k, v in sorted_items}     
        keys = list(sorted_degree_map.keys()).copy() 
        

        for key in keys:
            if key not in swap_nodes:
                distance_map = {}
                distance_map[0] = 0
                x = reverse_map[key] // N
                y = reverse_map[key] % N
                if x > 0:
                    distance_map[-N] = 0
                if x < N - 1:
                    distance_map[N] = 0
                if y > 0:
                    distance_map[-1] = 0
                if y < N - 1:
                    distance_map[1] = 0

                for dkey in distance_map.keys():
                    for nknode in sorted_degree_map[key]:
                        cur_pos = reverse_map[key] + dkey
                        distance_map[dkey] += ((cur_pos // N - reverse_map[nknode] // N) ** 2 + (cur_pos % N - reverse_map[nknode] % N) ** 2) ** 0.5
                
                # print(distance_map)
                items = distance_map.items()
                sorted_items = sorted(items, key=lambda x: x[1])
                sorted_distance_map = {k: v for k, v in sorted_items}
                dpos = list(sorted_distance_map.keys())[0]

                if dpos != 0:
                    if reverse_map[key] + dpos in pre_layer_incomplete_nodes.keys():
                        if pre_layer_incomplete_nodes[reverse_map[key] + dpos] not in swap_nodes:
                            swap_nodes.append(key)
                            swap_nodes.append(pre_layer_incomplete_nodes[reverse_map[key] + dpos])
                            swap_pairs.append((reverse_map[key], reverse_map[key] + dpos))
                            swap_pairs.append((reverse_map[key] + dpos, reverse_map[key]))
                            reverse_map[pre_layer_incomplete_nodes[reverse_map[key] + dpos]] = reverse_map[key]
                            pre_layer_incomplete_nodes[reverse_map[key]] = pre_layer_incomplete_nodes[reverse_map[key] + dpos]
                            pre_layer_incomplete_nodes[reverse_map[key] + dpos] = key
                            reverse_map[key] += dpos                   
                    else:
                        swap_nodes.append(key)
                        swap_pairs.append((reverse_map[key], reverse_map[key] + dpos))
                        del pre_layer_incomplete_nodes[reverse_map[key]]
                        pre_layer_incomplete_nodes[reverse_map[key] + dpos] = key
                        reverse_map[key] += dpos

        if len(swap_nodes) == 0:
            degree_map = {}
            for key in reverse_map.keys():
                degree_map[key] = len(list(origin_graph.neighbors(key)))


            items = degree_map.items()

            sorted_items = sorted(items, key=lambda x: x[1], reverse=True)

            sorted_degree_map = {k: v for k, v in sorted_items}     
            keys = list(sorted_degree_map.keys()).copy() 
            

            for key in keys:
                if key not in swap_nodes:
                    distance_map = {}
                    distance_map[0] = 0
                    x = reverse_map[key] // N
                    y = reverse_map[key] % N
                    if x > 0:
                        distance_map[-N] = 0
                    if x < N - 1:
                        distance_map[N] = 0
                    if y > 0:
                        distance_map[-1] = 0
                    if y < N - 1:
                        distance_map[1] = 0

                    for dkey in distance_map.keys():
                        cur_pos = reverse_map[key] + dkey
                        x = cur_pos // N
                        y = cur_pos % N
                        if x > 0:
                            if cur_pos - N not in pre_layer_incomplete_nodes.keys():
                                distance_map[dkey] += 1
                        if x < N - 1:
                            if cur_pos + N not in pre_layer_incomplete_nodes.keys():
                                distance_map[dkey] += 1
                        if y > 0:
                            if cur_pos - 1 not in pre_layer_incomplete_nodes.keys():
                                distance_map[dkey] += 1
                        if y < N - 1:
                            if cur_pos + 1 not in pre_layer_incomplete_nodes.keys():
                                distance_map[dkey] += 1
                    
                    items = distance_map.items()
                    sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
                    sorted_distance_map = {k: v for k, v in sorted_items}
                    dpos = list(sorted_distance_map.keys())[0]

                    if dpos != 0:
                        if reverse_map[key] + dpos in pre_layer_incomplete_nodes.keys():
                            if pre_layer_incomplete_nodes[reverse_map[key] + dpos] not in swap_nodes:
                                swap_nodes.append(key)
                                swap_nodes.append(pre_layer_incomplete_nodes[reverse_map[key] + dpos])
                                swap_pairs.append((reverse_map[key], reverse_map[key] + dpos))
                                swap_pairs.append((reverse_map[key] + dpos, reverse_map[key]))
                                reverse_map[pre_layer_incomplete_nodes[reverse_map[key] + dpos]] = reverse_map[key]
                                pre_layer_incomplete_nodes[reverse_map[key]] = pre_layer_incomplete_nodes[reverse_map[key] + dpos]
                                pre_layer_incomplete_nodes[reverse_map[key] + dpos] = key
                                reverse_map[key] += dpos                   
                        else:
                            swap_nodes.append(key)
                            swap_pairs.append((reverse_map[key], reverse_map[key] + dpos))
                            del pre_layer_incomplete_nodes[reverse_map[key]]
                            pre_layer_incomplete_nodes[reverse_map[key] + dpos] = key
                            reverse_map[key] += dpos          

    for rnode in pre_layer_incomplete_nodes.values():
        if rnode not in swap_nodes:
            swap_pairs.append((reverse_map[rnode], reverse_map[rnode]))

    graph = origin_graph.copy()
    net = create_net(pre_layer_incomplete_nodes, N)
    allocated_nodes = {}
    for key in pre_layer_incomplete_nodes.keys():
        allocated_nodes[pre_layer_incomplete_nodes[key]] = key

    # print(allocated_nodes.keys())
    extend_nodes = []
    isolated_nodes = []

    new_nodes = []
    for r in range(Round):
        old_isolated_nodes = []
        if r > 0:
            current_nodes_to_map = []

            # append allocated nodes into current nodes to map
            nodes_index = 0 
            for anode in allocated_nodes.keys():
                current_nodes_to_map.append(anode)
                nodes_index += 1

            dgraph_nodes = list(dgraph.nodes()).copy()
            for dnode in dgraph_nodes:
                if dnode not in graph.nodes() and len(list(dgraph.predecessors(dnode))) == 0:
                    succ_nodes = list(dgraph.successors(dnode)).copy()
                    for snode in succ_nodes:
                        dgraph.remove_edge(dnode, snode)
                    dgraph.remove_node(dnode)
            nkeys = list(nodes_to_be_measured.keys()).copy()
            # print(nkeys)
            for nnode in nkeys:
                if nnode not in dgraph.nodes():
                    # print(nnode, layer_index - nodes_to_be_measured[nnode], " layers measured", nodes_to_appear[nnode])
                    # if layer_index - nodes_to_be_measured[nnode] > RefreshBound:                                                
                    #     return net, {}, layer_graph_map[nodes_to_appear[nnode]][0], layer_graph_map[nodes_to_appear[nnode]][4], [], required_life_time, layer_graph_map[nodes_to_appear[nnode]][3], swap_pairs, cur_force_refresh_nodes_num, layer_graph_map[nodes_to_appear[nnode]][2], layer_graph_map, nodes_to_appear[nnode], layer_graph_map[nodes_to_appear[nnode]][1], layer_graph_map[nodes_to_appear[nnode]][6]  
                    del nodes_to_be_measured[nnode]                    

            front_nodes = []
            for dnode in dgraph.nodes():
                if len(list(dgraph.predecessors(dnode))) == 0:
                    front_nodes.append(dnode)
                    
            new_nodes = []
            for fnode in front_nodes:
                if fnode not in isolated_nodes:
                    if fnode not in current_nodes_to_map and fnode not in allocated_nodes_cache.keys():
                        select_flag = False
                        for cnode in current_nodes_to_map:
                            if graph.has_edge(cnode, fnode):
                                select_flag = True
                                break

                        if select_flag:
                            current_nodes_to_map.append(fnode)
                            nodes_index += 1
                            new_nodes.append(fnode)

            # if RefreshBound == 1 or layer_index == 0:
            # # if RefreshBound == 1:
            #     for fnode in front_nodes:
            #         if fnode not in isolated_nodes:
            #             if fnode not in current_nodes_to_map  and fnode not in allocated_nodes_cache.keys():
            #                 current_nodes_to_map.append(fnode)
            #                 nodes_index += 1  
            #                 new_nodes.append(fnode) 
            if layer_index == 0:
            # if RefreshBound == 1:
                for fnode in front_nodes:
                    if fnode not in isolated_nodes:
                        if fnode not in current_nodes_to_map  and fnode not in allocated_nodes_cache.keys():
                            current_nodes_to_map.append(fnode)
                            nodes_index += 1  
                            new_nodes.append(fnode) 
            if r == 1:
                for fnode in front_nodes:
                    if fnode not in isolated_nodes:
                        if fnode not in current_nodes_to_map  and fnode not in allocated_nodes_cache.keys():
                            current_nodes_to_map.append(fnode)
                            nodes_index += 1  
                            new_nodes.append(fnode) 
                            break
         
            if r > 1:
                # if MixedBound == 1 and RefreshBound == 1:
                for dnode in dgraph.nodes():
                    pdnodes = list(dgraph.predecessors(dnode)).copy()
                    if len(pdnodes):
                        flag = True
                        for pnode in pdnodes:
                            if pnode not in allocated_nodes.keys() and pnode not in allocated_nodes_cache.keys() or pnode not in front_nodes:
                                flag = False
                                break
                        # pnode = pdnodes[0]
                        if flag:
                            if dnode not in current_nodes_to_map and dnode not in allocated_nodes_cache.keys() and dnode not in isolated_nodes:
                                select_flag = False
                                for cnode in current_nodes_to_map:
                                    if graph.has_edge(cnode, dnode):
                                        select_flag = True
                                        break
                                if select_flag:
                                    # current_nodes_to_map.append(dnode)
                                    # nodes_index += 1
                                    new_nodes.append(dnode)
                
                last_dep_nodes = front_nodes
                if D_Flag:
                    Boundary = MixedBound
                else:
                    Boundary = min(MixedBound, 1)
                for i in range(Boundary):
                    if i > r - 2 and nodes_index > 3 * N * N:
                        break
                    last_dep_nodes_copy = last_dep_nodes.copy()
                    for dnode in dgraph.nodes():
                        pdnodes = list(dgraph.predecessors(dnode)).copy()
                        if len(pdnodes):
                            flag = True
                            for pnode in pdnodes:
                                # pnode not in current_nodes_to_map or 
                                if pnode not in last_dep_nodes_copy:
                                    flag = False
                                    break

                            if flag:
                                if dnode not in last_dep_nodes:
                                    last_dep_nodes.append(dnode)

                    for lnode in last_dep_nodes:
                        if lnode not in current_nodes_to_map and lnode not in allocated_nodes_cache.keys() and lnode not in isolated_nodes:
                            # select_flag = False
                            # for cnode in current_nodes_to_map:
                            #     if graph.has_edge(cnode, lnode):
                            #         select_flag = True
                            #         break

                            # if select_flag:
                            current_nodes_to_map.append(lnode)
                            nodes_index += 1
                            new_nodes.append(lnode)  
        else:
            current_nodes_to_map = []
            for anode in allocated_nodes.keys():
                current_nodes_to_map.append(anode) 

        current_graph_to_map = nx.subgraph(graph, current_nodes_to_map).copy()
        components = list(nx.connected_components(current_graph_to_map)).copy()

        for component in components:

            allocated_incomplete_nodes_origin =[]
            allocated_incomplete_nodes = []

            for cnode in list(component):
                if cnode in allocated_nodes.keys():
                    neigh_cnodes = list(graph.neighbors(cnode))
                    if len(neigh_cnodes):
                        allocated_incomplete_nodes.append(cnode)
                        allocated_incomplete_nodes_origin.append(cnode)

            if len(allocated_incomplete_nodes) == 0:
                for cnode in list(component):
                    if cnode in front_nodes:
                        begin_node = cnode
                        empty_nnodes = []

                        for nnode in net.nodes():
                            if net.nodes[nnode]['node_val'] == Empty:
                                empty_nnodes.append(nnode)
                        
                        empty_nnodes_size =  len(empty_nnodes)
                        if empty_nnodes_size == 0:
                            continue
                        allocated_incomplete_nodes_origin = [begin_node]
                        chosen_pos = empty_nnodes[random.randint(0, empty_nnodes_size - 1)]
                        allocated_nodes[begin_node] = chosen_pos
                        net.nodes[chosen_pos]['node_val'] = begin_node
                        net.nodes[chosen_pos]['node_color'] = 'blue'
                        break



            # allocated_incomplete_nodes = allocated_incomplete_nodes_origin.copy()
            # route the allocated incomplete nodes
            allocated_incomplete_nodes_origin_copy = allocated_incomplete_nodes_origin.copy()
            while len(allocated_incomplete_nodes_origin):
                allocated_incomplete_node = allocated_incomplete_nodes_origin[0]
                allocated_incomplete_nodes_origin.remove(allocated_incomplete_node)        

                # check again whether it is incomplete
                if len(list(graph.neighbors(allocated_incomplete_node))) == 0:
                    graph.remove_node(allocated_incomplete_node)
                    current_graph_to_map.remove_node(allocated_incomplete_node)
                    continue  

                neigh_allocated_nodes = list(graph.neighbors(allocated_incomplete_node))

                
                # divide neighbor nodes into unallocated list and allocated list
                neigh_nodes = list(graph.neighbors(allocated_incomplete_node)).copy()

                allocated_neigh_nodes = []
                for neigh_node in neigh_nodes:
                    if neigh_node in current_nodes_to_map:
                        if neigh_node in allocated_nodes.keys():
                            allocated_neigh_nodes.append(neigh_node)

                '''
                step1: route the allocated incomplete node to the allocated neighbor nodes
                '''
                for allocated_neigh_node in allocated_neigh_nodes:
                    src_pos = allocated_nodes[allocated_incomplete_node]
                    target_pos = allocated_nodes[allocated_neigh_node]
                    node_set = [src_pos, target_pos]
                    for nnode in net.nodes():
                        if net.nodes[nnode]['node_val'] == Empty:
                            node_set.append(nnode)

                    # find shortest path between allocated incomplete node to the allocated neighbor node
                    route_net = nx.subgraph(net, node_set)
                    has_path = nx.has_path(route_net, src_pos, target_pos)  
                    if has_path:
                        simple_path = nx.shortest_path(route_net, src_pos, target_pos)
                        pre_node = src_pos
                        for snode in simple_path[1:]:
                            if snode != target_pos:
                                net.nodes[snode]['node_val'] = Auxiliary
                            net[pre_node][snode]['color'] = 'red'
                            pre_node = snode
                        graph.remove_edge(allocated_incomplete_node, allocated_neigh_node)
                        current_graph_to_map.remove_edge(allocated_incomplete_node, allocated_neigh_node)
                        if len(list(graph.neighbors(allocated_neigh_node))) == 0:
                            graph.remove_node(allocated_neigh_node)  
                            current_graph_to_map.remove_node(allocated_neigh_node)
                            if allocated_neigh_node in allocated_incomplete_nodes_origin:
                                allocated_incomplete_nodes_origin.remove(allocated_neigh_node) 
                                '''
                step3: sort allocated incomplete nodes with its neighbor's quantity
                '''

                def neigh_quantity(node):
                    return len(list(graph.neighbors(node)))

                allocated_incomplete_nodes_origin = sorted(allocated_incomplete_nodes_origin, key=neigh_quantity, reverse = True)

            allocated_incomplete_nodes_origin = []
            for anode in allocated_incomplete_nodes_origin_copy:
                if anode in graph.nodes():
                    allocated_incomplete_nodes_origin.append(anode)

            # map the allocated incomplete nodes
            while len(allocated_incomplete_nodes_origin):
                allocated_incomplete_node = allocated_incomplete_nodes_origin[0]
                allocated_incomplete_nodes_origin.remove(allocated_incomplete_node)        

                # check again whether it is incomplete
                if len(list(graph.neighbors(allocated_incomplete_node))) == 0:
                    graph.remove_node(allocated_incomplete_node)
                    current_graph_to_map.remove_node(allocated_incomplete_node)
                    continue  

                # neigh_allocated_nodes = list(graph.neighbors(allocated_incomplete_node))

                
                # divide neighbor nodes into unallocated list and allocated list
                neigh_nodes = list(graph.neighbors(allocated_incomplete_node)).copy()

                unallocated_neigh_nodes = []
                for neigh_node in neigh_nodes:
                    if neigh_node in current_nodes_to_map:
                        if neigh_node not in allocated_nodes.keys():
                            unallocated_neigh_nodes.append(neigh_node)

                '''
                step2: find a path to allocate to unallocated neighbor nodes
                '''
                search_set = []
                search_index = 0
                search_node = SearchNode(net.copy(), [allocated_nodes[allocated_incomplete_node]], allocated_incomplete_nodes_origin, N)
                heapq.heappush(search_set, search_node)
                while len(search_set):
                    # get the search node with largest free space
                    search_node = heapq.heappop(search_set)
                    
                    # find a available solution
                    if search_node.f >= len(unallocated_neigh_nodes):
                        break
                    
                    # reach search upper bound, stop searching
                    if search_index > SearchUpperBound:
                        # print("reach search upper bound break")
                        break
                    search_index += 1

                    # keep searching, adding new search node into search set
                    if search_node.f > nnode in dgraph.nodes() and len(list(dgraph.predecessors(nnode))) == 0  and nnode not in graph.nodes() or 0:
                        search_net = search_node.net
                        search_path = search_node.path

                        untake_pos_list = count_pos_untake(search_net, search_path[-1], N)
                        for untake_pos in untake_pos_list:
                            
                            # update new net and new path
                            new_net = search_net.copy()
                            new_net.add_edge(search_path[-1], untake_pos) 
                            new_path = search_path.copy()
                            new_path.append(untake_pos)   
                            new_net.nodes[untake_pos]['node_val'] = Auxiliary
                            new_node = SearchNode(new_net, new_path, allocated_incomplete_nodes_origin, N)
                            heapq.heappush(search_set, new_node)

                # allocate the unallocated nodes to the free space along the path
                if search_node.f:
                    net = search_node.net.copy()
                    path = search_node.path.copy()
                    free_pos_set = search_node.free_space.copy()
                    
                    # mark the path
                    pre_node = allocated_nodes[allocated_incomplete_node]
                    for pnode in path[1:]:
                        net[pre_node][pnode]['color'] = 'red'
                        pre_node = pnode

                    for free_pos in free_pos_set:
                        if len(unallocated_neigh_nodes) == 0:
                            break

                        pre_pos = find_pre_pos(path, free_pos, N)
                        
                        # pre position unfound, that is impossible actually
                        if pre_pos == -1:
                            continue

                        unallocated_neigh_node = unallocated_neigh_nodes[0]
                        unallocated_neigh_nodes.remove(unallocated_neigh_node)                   
                        net.nodes[free_pos]['node_val'] = unallocated_neigh_node
                        net.nodes[free_pos]['node_color'] = 'blue'
                        net[pre_pos][free_pos]['color'] = 'red'
                        allocated_nodes[unallocated_neigh_node] = free_pos
                        graph.remove_edge(allocated_incomplete_node, unallocated_neigh_node)
                        current_graph_to_map.remove_edge(allocated_incomplete_node, unallocated_neigh_node)
                        if len(list(graph.neighbors(unallocated_neigh_node))):
                            allocated_incomplete_nodes_origin.append(unallocated_neigh_node)

                '''
                step3: sort allocated incomplete nodes with its neighbor's quantity
                '''

                def neigh_quantity(node):
                    return len(list(graph.neighbors(node)))

                allocated_incomplete_nodes_origin = sorted(allocated_incomplete_nodes_origin, key=neigh_quantity, reverse = True)

            
        for allocated_node in allocated_nodes.keys():
            if allocated_node in graph.nodes():
                neigh_allocated_nodes = list(graph.neighbors(allocated_node))
                if len(neigh_allocated_nodes) == 1 and neigh_allocated_nodes[0] not in allocated_nodes.keys() and neigh_allocated_nodes[0] not in allocated_nodes_cache.keys():
                    if allocated_node not in extend_nodes:
                        extend_nodes.append(allocated_node)
                        # print("extend node", allocated_node)

        # delete the isolated nodes
        for nnode in net.nodes():
            if net.nodes[nnode]['node_val'] not in refresh_nodes and net.nodes[nnode]['node_val'] not in extend_nodes:
                if net.nodes[nnode]['node_val'] != Empty and net.nodes[nnode]['node_val'] != Auxiliary:
                    if r > 0 and is_isolated(net, nnode, N) and nnode not in pre_layer_incomplete_nodes.keys():
                        if net.nodes[nnode]['node_val'] in graph.nodes():
                            isolated_nodes.append(net.nodes[nnode]['node_val'])
                            del allocated_nodes[net.nodes[nnode]['node_val']] 
                            net.nodes[nnode]['node_val'] = Empty  
                            net.nodes[nnode]['node_color'] = 'lightgray' 
                        

                    if r == 0 and is_isolated(net, nnode, N) and nnode in pre_layer_incomplete_nodes.keys() and net.nodes[nnode]['node_val'] not in refresh_nodes:
                        neigh_inodes = graph.neighbors(net.nodes[nnode]['node_val'])
                        flag = True
                        for ninode in neigh_inodes:
                            if ninode not in allocated_nodes and ninode not in allocated_nodes_cache.keys():
                                flag = False
                                break
                        if flag: 
                            # print("isolated allocated node", net.nodes[nnode]['node_val'])
                            old_isolated_nodes.append(net.nodes[nnode]['node_val'])
                            allocated_nodes_cache[net.nodes[nnode]['node_val']] = reverse_map_origin[net.nodes[nnode]['node_val']] 
                            del allocated_nodes[net.nodes[nnode]['node_val']] 
                            net.nodes[nnode]['node_val'] = Empty  
                            net.nodes[nnode]['node_color'] = 'lightgray'  
                        
        flag = True
        independent_nodes = []
        for ne in net.edges():
            if net[ne[0]][ne[1]] == 'red':
                flag = False
                break
        if flag:
        # if RefreshBound == 1:
            index = 0
            for cnode in current_nodes_to_map:
                if cnode not in allocated_nodes.keys() and len(list(dgraph.predecessors(cnode))) == 0 and index < 1:
                    flag1 = False
                    for anode in allocated_nodes.keys():
                        if graph.has_edge(cnode, anode):
                            flag1 = True
                            break
                    if flag1: 
                        # print("cnode", cnode)
                        begin_node = cnode
                        empty_nnodes = []

                        for nnode in net.nodes():
                            if net.nodes[nnode]['node_val'] == Empty:
                                empty_nnodes.append(nnode)
                        
                        empty_nnodes_size =  len(empty_nnodes)
                        if empty_nnodes_size == 0:
                            continue

                        chosen_pos = empty_nnodes[random.randint(0, empty_nnodes_size - 1)]
                        allocated_nodes[begin_node] = chosen_pos
                        net.nodes[chosen_pos]['node_val'] = begin_node
                        net.nodes[chosen_pos]['node_color'] = 'blue'
                        independent_nodes.append(chosen_pos)
                        index += 1

        # clear graph nodes
        all_nodes = list(graph.nodes()).copy()
        for gnode in all_nodes:
            if len(list(graph.neighbors(gnode))) == 0:
                graph.remove_node(gnode)

    allocated_nodes_incomplete = {}
    inter_edges = []

    extend_nodes_map = {}
    for allocated_node in allocated_nodes.keys():
        if allocated_node in graph.nodes():
            neigh_allocated_nodes = list(graph.neighbors(allocated_node))
            if len(neigh_allocated_nodes) == 1 and neigh_allocated_nodes[0] not in allocated_nodes.keys() and neigh_allocated_nodes[0] in new_nodes:
                extend_nodes_map[allocated_node] = neigh_allocated_nodes[0]

    if MixedBound == 0:
        while(1):
            del_extend_nodes = []
            ekeys = list(extend_nodes_map.keys()).copy()
            for ekey in ekeys:
                nekey = extend_nodes_map[ekey]
                pre_neigh_nodes = dgraph.predecessors(nekey)
                for pnnode in pre_neigh_nodes:
                    if pnnode not in extend_nodes_map.keys():
                        del extend_nodes_map[ekey]
                        del_extend_nodes.append(ekey)
                        break
            if len(del_extend_nodes) == 0:
                break

    for allocated_node in allocated_nodes.keys():
        if allocated_node in graph.nodes():
            if allocated_node in extend_nodes_map.keys():
                neigh_allocated_nodes = list(graph.neighbors(allocated_node))
                allocated_nodes_incomplete[allocated_nodes[allocated_node]] = neigh_allocated_nodes[0]
                graph_nodes_pos[neigh_allocated_nodes[0]] = layer_index
                if neigh_allocated_nodes[0] not in nodes_to_appear.keys():
                    nodes_to_appear[neigh_allocated_nodes[0]] = layer_index
                # allocated_nodes_cache[neigh_allocated_nodes[0]] = allocated_nodes[allocated_node]
                graph.remove_edge(allocated_node, neigh_allocated_nodes[0])
                graph.remove_node(allocated_node)
                if allocated_node in dgraph.nodes and len(list(dgraph.predecessors(allocated_node))):
                    nodes_to_be_measured[allocated_node] = layer_index
            else:
                allocated_nodes_incomplete[allocated_nodes[allocated_node]] = allocated_node
        else:
            if allocated_node in dgraph.nodes and len(list(dgraph.predecessors(allocated_node))):
                nodes_to_be_measured[allocated_node] = layer_index        
            
        if allocated_node in pre_layer_incomplete_nodes.values():
            if allocated_node in graph_nodes_pos.keys():
                required_life_time = max(required_life_time, layer_index - graph_nodes_pos[allocated_node])
            inter_edges.append((allocated_nodes[allocated_node], graph_nodes_pos[allocated_node], layer_index))
    
    # update graph nodes_pos
    for nnode in net.nodes():
        if net.nodes[nnode]['node_val']:
            graph_nodes_pos[net.nodes[nnode]['node_val']] = layer_index

    new_nodes = []
    for allocated_node in allocated_nodes.keys():
        if allocated_node not in nodes_to_appear.keys():
            nodes_to_appear[allocated_node] = layer_index
            new_nodes.append(allocated_node)
    # print(new_nodes)

    dgraph_nodes = list(dgraph.nodes()).copy()
    for dnode in dgraph_nodes:
        if dnode not in graph.nodes() and len(list(dgraph.predecessors(dnode))) == 0:
            succ_nodes = list(dgraph.successors(dnode)).copy()
            for snode in succ_nodes:
                dgraph.remove_edge(dnode, snode)
            dgraph.remove_node(dnode)
    nkeys = list(nodes_to_be_measured.keys()).copy()
    for nnode in nkeys:
        if nnode not in dgraph.nodes():
            # print(nnode, layer_index - nodes_to_be_measured[nnode], " layers measured", nodes_to_appear[nnode])
            # if layer_index - nodes_to_be_measured[nnode] > RefreshBound:                     
            #     return net, {}, layer_graph_map[nodes_to_appear[nnode]][0], layer_graph_map[nodes_to_appear[nnode]][4], [], required_life_time, layer_graph_map[nodes_to_appear[nnode]][3], swap_pairs, cur_force_refresh_nodes_num, layer_graph_map[nodes_to_appear[nnode]][2], layer_graph_map, nodes_to_appear[nnode], layer_graph_map[nodes_to_appear[nnode]][1], layer_graph_map[nodes_to_appear[nnode]][6]          
            del nodes_to_be_measured[nnode]   
    return net, allocated_nodes_incomplete, graph, graph_nodes_pos, inter_edges, required_life_time, allocated_nodes_cache, swap_pairs, cur_force_refresh_nodes_num, nodes_to_be_measured, layer_graph_map, layer_index + 1, dgraph, nodes_to_appear

    # P = 0.6 / RefreshBound ** 0.5 + 0.4 QAOA
def map_route(a, graph, dgraph, NQubit, N, Refresh, RefreshBound, D_Flag, Braiding, P_const):
    M = 1
    swap_map = {}
    required_life_time = 0
    refresh_begin_list = []
    refresh_end_list = []

    layer_index = 0

    net_list = []
    inter_edges_list = []
    layer_list = []
    graph_nodes_pos = {}
    left_graph_nodes_list = []

    allocated_nodes_cache = {}
    pre_graph = list(graph.edges()) 
    nodes_to_be_measured = {}
    nodes_to_appear = {}
    layer_graph_map = {}

    P = 1
    MixedBound = M
    succ_rate = 0
    pre_nodes_count = 0
    if a == 'RCA':
        M += 1
    # if N <= 3:
    #     M = 2
    while len(graph.nodes()):
        # if there is connection between two same position then directly fusion them
        exit_flag = 1
        for edge in graph.edges():
            if edge[0] in allocated_nodes_cache.keys() and edge[1] in allocated_nodes_cache.keys() and allocated_nodes_cache[edge[0]] == allocated_nodes_cache[edge[1]]:
                exit_flag = exit_flag
            else:
                exit_flag = 0
                break
        if exit_flag == 1:
            break
        
        for edge in graph.edges():
            if edge[0] in allocated_nodes_cache.keys() and edge[1] in allocated_nodes_cache.keys() and allocated_nodes_cache[edge[0]] == allocated_nodes_cache[edge[1]]:
                if len(list(graph.neighbors(edge[0]))) == 1 and len(list(graph.neighbors(edge[1]))) == 1:
                    graph.remove_edge(edge[0] ,edge[1])

        left_graph_nodes_list.append(len(graph.nodes()))
        layer_list.append(layer_index)

        # remove complete nodes in allocated_nodes_cache
        akeys = list(allocated_nodes_cache.keys())
        for gnode in akeys:
            if gnode not in graph.nodes() or len(list(graph.neighbors(gnode))) == 0:
                del allocated_nodes_cache[gnode]

        # one layer map and route
        old_layer_index = layer_index
        # print('mixedbound', MixedBound)
        pre_nodes_count = len(graph.nodes())
        net, allocated_incomplete_nodes, graph, graph_nodes_pos, inter_edges, required_life_time,  allocated_nodes_cache, swap_pairs, cur_force_refresh_nodes_num, nodes_to_be_measured, layer_graph_map, layer_index, dgraph, nodes_to_appear = one_layer_map_route(graph, dgraph, allocated_nodes_cache, graph_nodes_pos, layer_index, N, required_life_time, Refresh, RefreshBound, NQubit, P, D_Flag, Braiding, nodes_to_be_measured, layer_graph_map, MixedBound, nodes_to_appear)
        print(old_layer_index, len(list(graph.nodes())))
        if pre_nodes_count == len(list(graph.nodes())):
            same_count += 1
        else:
            same_count = 0
        # print("next layer index,", layer_index)
        if old_layer_index == layer_index - 1:
            succ_rate += 1
            net_list.append(net)
            P = min(cur_force_refresh_nodes_num / (N ** 2) + P_const, 1)
            swap_map[layer_index - 1] = swap_pairs
            inter_edges_list.append(inter_edges)

            # add allocated incomplete nodes to cache  
            for apos in allocated_incomplete_nodes.keys():
                allocated_nodes_cache[allocated_incomplete_nodes[apos]] = apos
            MixedBound = M
        else:
            succ_rate = 0
            net_list = net_list[0: layer_index]
            for i in range(layer_index, old_layer_index):
                del swap_map[i]
            # swap_map[layer_index - 1] = swap_pairs
            inter_edges_list = inter_edges_list[0: layer_index]
            P = layer_graph_map[layer_index][5]
            MixedBound = 1
        if NQubit == 36 and N == 6 and layer_index > 10000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, swap_map
        if NQubit == 64 and layer_index > 10000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, swap_map
        if layer_index > 10000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, swap_map

    return net_list, layer_index, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, swap_map
