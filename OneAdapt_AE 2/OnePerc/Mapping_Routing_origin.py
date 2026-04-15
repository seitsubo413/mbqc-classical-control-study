import networkx as nx
import matplotlib.pyplot as plt
import random
import math
import heapq

Empty = 1e1000
Auxiliary = -1
SearchUpperBound = 40
Round = 2
Average_Depth = 1


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

def one_layer_map_route(origin_graph, pre_layer_incomplete_nodes, dgraph, allocated_nodes_cache, graph_nodes_pos, layer_index, N, required_life_time, max_measure_delay):
    incomplete_nodes_allocated_size = 0
    graph = origin_graph.copy()
    net = create_net(pre_layer_incomplete_nodes, N)
    allocated_nodes = {}
    for key in pre_layer_incomplete_nodes.keys():
        allocated_nodes[pre_layer_incomplete_nodes[key]] = key
        if len(list(graph.neighbors(pre_layer_incomplete_nodes[key]))):
            incomplete_nodes_allocated_size += 1

    for r in range(Round):
        current_nodes_to_map = []

        # update dgraph
        parent_values = set()
        for gnode in graph.nodes():
            parent_values.add(graph.nodes[gnode]['parent'])

        dgraph_nodes = list(dgraph.nodes()).copy()

        for dnode in dgraph_nodes:
            if dnode not in parent_values:
                succ_nodes = list(dgraph.successors(dnode)).copy()
                for snode in succ_nodes:
                    dgraph.remove_edge(dnode, snode)
                    
                dgraph.remove_node(dnode)
                
        
        # get available parents
        avail_parent = set()
        cur_layer_parent =set()
        for dnode in dgraph.nodes():
            if  len(list(dgraph.predecessors(dnode))) == 0:
                cur_layer_parent.add(dnode)
        copy_cur_layer_parent = cur_layer_parent.copy()
        avail_parent = avail_parent | copy_cur_layer_parent

        for i in range(Average_Depth):
            cur_layer_parent = set()
            for parent in copy_cur_layer_parent:
                for suc_parent in dgraph.successors(parent):
                    cur_layer_parent.add(suc_parent)
            copy_cur_layer_parent = cur_layer_parent.copy()
            avail_parent = avail_parent | copy_cur_layer_parent

        # append allocated nodes into current nodes to map
        nodes_index = 0 
        for anode in allocated_nodes.keys():
                current_nodes_to_map.append(anode) 
                nodes_index += 1

        # append extra graph nodes to current nodes to map according to available parents
        for gnode in graph.nodes():
            if graph.nodes[gnode]['parent'] in avail_parent and gnode not in allocated_nodes_cache.keys():
                if gnode not in current_nodes_to_map and nodes_index <= N * N * 12:
                    current_nodes_to_map.append(gnode)
                    nodes_index += 1


        current_graph_to_map = nx.subgraph(graph, current_nodes_to_map).copy()
        components = list(nx.connected_components(current_graph_to_map))

        for component in components:
            # componet contain only one node
            if len(list(component)) == 1:
                # print("continue")
                continue

            allocated_incomplete_nodes =[]

            for cnode in list(component):
                if cnode in allocated_nodes.keys():
                    if len(list(graph.neighbors(cnode))):
                        allocated_incomplete_nodes.append(cnode)
            
            if len(allocated_incomplete_nodes) == 0:
                # allocate the beginning node in net
                # if incomplete_nodes_allocated_size >= math.ceil(N * N * P):
                #     break
                begin_node = list(component)[0]
                allocated_incomplete_nodes = [begin_node]
                incomplete_nodes_allocated_size += 1
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

            # map and route the allocated incomplete nodes
            while len(allocated_incomplete_nodes):
                # print("enter")
                allocated_incomplete_node = allocated_incomplete_nodes[0]
                allocated_incomplete_nodes.remove(allocated_incomplete_node)        

                # check again whether it is incomplete
                if len(list(graph.neighbors(allocated_incomplete_node))) == 0:
                    graph.remove_node(allocated_incomplete_node)
                    if allocated_incomplete_node in graph_nodes_pos.keys():
                        max_measure_delay = max(max_measure_delay, layer_index - graph_nodes_pos[allocated_incomplete_node])
                    current_graph_to_map.remove_node(allocated_incomplete_node)
                    continue  
                
                # divide neighbor nodes into unallocated list and allocated list
                neigh_nodes = list(current_graph_to_map.neighbors(allocated_incomplete_node)).copy()

                allocated_neigh_nodes = []
                unallocated_neigh_nodes = []
                for neigh_node in neigh_nodes:
                    if neigh_node in current_nodes_to_map:
                        if neigh_node in allocated_nodes.keys():
                            allocated_neigh_nodes.append(neigh_node)
                        else:
                            unallocated_neigh_nodes.append(neigh_node)
                # print("allocated nodes,", allocated_neigh_nodes)
                # print("unallocated nodes,", unallocated_neigh_nodes)
                '''
                step1: route the allocated incomplete node to the allocated neighbor nodes
                '''
                for allocated_neigh_node in allocated_neigh_nodes:
                    src_pos = allocated_nodes[allocated_incomplete_node]
                    target_pos = allocated_nodes[allocated_neigh_node]
                    node_set = [src_pos, target_pos]
                    for nnode in net.nodes():
                        if net.nodes[nnode]['node_val'] == Empty:
                        # if net.nodes[nnode]['node_val'] == Empty and not lead_to_blockness(net, allocated_incomplete_nodes, nnode):
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
                            if allocated_neigh_node in graph_nodes_pos.keys():
                                max_measure_delay = max(max_measure_delay, layer_index - graph_nodes_pos[allocated_neigh_node])
                            current_graph_to_map.remove_node(allocated_neigh_node)
                            if allocated_neigh_node in allocated_incomplete_nodes:
                                allocated_incomplete_nodes.remove(allocated_neigh_node) 
                            incomplete_nodes_allocated_size -= 1

                '''
                step2: find a path to allocate to unallocated neighbor nodes
                '''
                search_set = []
                search_index = 0
                search_node = SearchNode(net.copy(), [allocated_nodes[allocated_incomplete_node]], allocated_incomplete_nodes, N)
                heapq.heappush(search_set, search_node)
                while len(search_set):
                    # get the search node with largest free space
                    search_node = heapq.heappop(search_set)
                    
                    # find a available solution
                    if search_node.f >= len(unallocated_neigh_nodes):
                        break
                    
                    # reach search upper bound, stop searching
                    if search_index > SearchUpperBound:
                        print("reach search upper bound break")
                        break
                    search_index += 1

                    # keep searching, adding new search node into search set
                    if search_node.f > 0:
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
                            new_node = SearchNode(new_net, new_path, allocated_incomplete_nodes, N)
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
                            allocated_incomplete_nodes.append(unallocated_neigh_node)
                            incomplete_nodes_allocated_size += 1

                
                if len(list(graph.neighbors(allocated_incomplete_node))) == 0:
                    incomplete_nodes_allocated_size -= 1 
                '''
                step3: sort allocated incomplete nodes with its neighbor's quantity
                '''

                def neigh_quantity(node):
                    return len(list(graph.neighbors(node)))

                allocated_incomplete_nodes = sorted(allocated_incomplete_nodes, key=neigh_quantity, reverse = True)

        # delete the isolated nodes
        for nnode in net.nodes():
            if net.nodes[nnode]['node_val'] != Empty and net.nodes[nnode]['node_val'] != Auxiliary:
                if is_isolated(net, nnode, N) and nnode not in pre_layer_incomplete_nodes.keys():
                    del allocated_nodes[net.nodes[nnode]['node_val']] 
                    net.nodes[nnode]['node_val'] = Empty  
                    net.nodes[nnode]['node_color'] = 'lightgray'    


    # clear graph nodes
    all_nodes = list(graph.nodes()).copy()
    for gnode in all_nodes:
        if len(list(graph.neighbors(gnode))) == 0:
            graph.remove_node(gnode)
            if gnode in graph_nodes_pos.keys():
                max_measure_delay = max(max_measure_delay, layer_index - graph_nodes_pos[gnode])

    allocated_nodes_incomplete = {}
    inter_edges = []
    for allocated_node in allocated_nodes.keys():
        if allocated_node in graph.nodes():
            neigh_allocated_nodes = list(graph.neighbors(allocated_node))
            if len(neigh_allocated_nodes) == 1 and neigh_allocated_nodes[0] not in allocated_nodes.keys() and neigh_allocated_nodes[0] not in allocated_nodes_cache.keys():
                allocated_nodes_incomplete[allocated_nodes[allocated_node]] = neigh_allocated_nodes[0]
                graph_nodes_pos[neigh_allocated_nodes[0]] = layer_index
                graph.remove_edge(allocated_node, neigh_allocated_nodes[0])
                graph.remove_node(allocated_node)
                if allocated_node in graph_nodes_pos.keys():
                    max_measure_delay = max(max_measure_delay, layer_index - graph_nodes_pos[allocated_node])
            else:
                allocated_nodes_incomplete[allocated_nodes[allocated_node]] = allocated_node
        if allocated_node in pre_layer_incomplete_nodes.values():
            if allocated_node in graph_nodes_pos.keys():
                required_life_time = max(required_life_time, layer_index - graph_nodes_pos[allocated_node])
                # print("r1,", required_life_time)
            inter_edges.append((allocated_nodes[allocated_node], graph_nodes_pos[allocated_node], layer_index))
    
    # update graph nodes_pos
    for nnode in net.nodes():
        if net.nodes[nnode]['node_val']:
            graph_nodes_pos[net.nodes[nnode]['node_val']] = layer_index
    return net, allocated_nodes_incomplete, graph, graph_nodes_pos, inter_edges, required_life_time, max_measure_delay

def refresh(allocated_nodes_cache_origin, graph_nodes_pos, layer_index, N, required_life_time):
    refresh_index = 0
    refresh_inter_edges_list = []
    refresh_net_list = []
    allocated_nodes_cache = allocated_nodes_cache_origin.copy()
    allocated_keys = list(allocated_nodes_cache.keys())
    while len(allocated_keys):
        refresh_index += 1
        inter_edges = []
        net = create_net({}, N)
        for akey in allocated_keys:
            akey_pos = allocated_nodes_cache[akey]
            if net.nodes[akey_pos]['node_val'] == Empty:
                net.nodes[akey_pos]['node_val'] = akey
                del allocated_nodes_cache[akey]
                inter_edges.append((akey_pos, graph_nodes_pos[akey], layer_index))
                if akey in graph_nodes_pos.keys():
                    required_life_time = max(required_life_time, layer_index - graph_nodes_pos[akey])
                    # print("r2,", required_life_time)
                graph_nodes_pos[akey] = layer_index
        refresh_inter_edges_list.append(inter_edges)
        refresh_net_list.append(net)
        layer_index += 1
        allocated_keys = list(allocated_nodes_cache.keys())
    print("refresh", refresh_index)
    return layer_index, refresh_net_list, graph_nodes_pos, refresh_inter_edges_list, required_life_time


def map_route(graph, dgraph, NQubit, N, Refresh, RefreshBound):
    required_life_time = 0
    refresh_begin_list = []
    refresh_end_list = []
    pre_graph = graph.copy()

    P = 0.05
    layer_index = 0
    refresh_index = 0

    net_list = []
    inter_edges_list = []
    layer_list = []
    graph_nodes_pos = {}
    left_graph_nodes_list = []

    allocated_nodes_cache = {}
    allocated_incomplete_nodes = {}
    pre_nodes_size = 0
    max_measure_delay = 0
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

        # print("layer", layer_index, ":", len(graph.nodes()), "nodes left in graph,")
        left_graph_nodes_list.append(len(graph.nodes()))
        layer_list.append(layer_index)

        # remove complete nodes in allocated_nodes_cache
        akeys = list(allocated_nodes_cache.keys())
        for gnode in akeys:
            if gnode not in graph.nodes() or len(list(graph.neighbors(gnode))) == 0:
                del allocated_nodes_cache[gnode]
        


        # get allocated incomplete nodes from allocated nodes cache
        allocated_incomplete_nodes.clear()
        index = 0
        keys = list(allocated_nodes_cache.keys()).copy()
        while len(keys):
            if index >= N * N * P:
                break
            key = keys[0]
            keys.remove(key)
            if allocated_nodes_cache[key] not in allocated_incomplete_nodes.keys():
                flag = False
                for kkey in keys:
                    if graph.has_edge(key, kkey) and allocated_nodes_cache[kkey] not in allocated_incomplete_nodes.keys():
                        allocated_incomplete_nodes[allocated_nodes_cache[kkey]] = kkey
                        del allocated_nodes_cache[kkey]  
                        keys.remove(kkey)
                        index += 1 
                        flag = True
                if flag:
                    allocated_incomplete_nodes[allocated_nodes_cache[key]] = key
                    del allocated_nodes_cache[key]
                    index += 1
            else:
                continue
        keys = list(allocated_nodes_cache.keys()).copy()
        while len(keys):
            if index >= N * N * P:
                break
            key = keys[0]
            keys.remove(key)
            if allocated_nodes_cache[key] not in allocated_incomplete_nodes.keys():
                allocated_incomplete_nodes[allocated_nodes_cache[key]] = key
                del allocated_nodes_cache[key]
                index += 1
            else:
                continue
        
        # one layer map and route
        net, allocated_incomplete_nodes, graph, graph_nodes_pos, inter_edges, required_life_time, max_measure_delay = one_layer_map_route(graph, allocated_incomplete_nodes, dgraph, allocated_nodes_cache, graph_nodes_pos, layer_index, N, required_life_time, max_measure_delay)
        net_list.append(net)
        inter_edges_list.append(inter_edges)

        # add allocated incomplete nodes to cache  
        for apos in allocated_incomplete_nodes.keys():
            allocated_nodes_cache[allocated_incomplete_nodes[apos]] = apos
        
        print(len(list(graph.nodes())))
        # if pre_graph == list(graph.edges()):
        #     save_net(net, layer_index, N)
        #     break
        pre_graph = list(graph.edges()).copy()
        layer_index += 1
        refresh_index += 1
        if refresh_index >= RefreshBound and Refresh:
            refresh_begin_list.append(layer_index)
            layer_index, refresh_net_list, graph_nodes_pos, refresh_inter_edges_list, required_life_time = refresh(allocated_nodes_cache, graph_nodes_pos, layer_index, N, required_life_time)
            refresh_end_list.append(layer_index)
            net_list = net_list + refresh_net_list
            inter_edges_list = inter_edges_list + refresh_inter_edges_list
            refresh_index = 0
        # print(required_life_time)
        if NQubit == 36 and N == 6 and layer_index > 10000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay
        if NQubit == 64 and layer_index > 10000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay
        if layer_index > 20000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay
    return net_list, layer_index, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay