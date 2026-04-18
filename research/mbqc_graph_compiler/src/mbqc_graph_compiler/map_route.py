"""
Maps and routes a reduced-degree graph state onto an N×N 2D grid layout.

Returns layer_index (physical depth), required_lifetime_layers, and
max_measure_delay_layers used for hardware budget analysis.
"""
from __future__ import annotations

import heapq
import math
import random

import networkx as nx

Empty = 1e1000
Auxiliary = -1
SearchUpperBound = 40
Round = 2
Average_Depth = 1


def _count_pos_untake(net: nx.Graph, pos: int, N: int) -> list[int]:
    pos_i = pos // N
    pos_j = pos % N
    untake = []
    if pos_i > 0 and net.nodes[(pos_i - 1) * N + pos_j]["node_val"] == Empty:
        untake.append((pos_i - 1) * N + pos_j)
    if pos_j > 0 and net.nodes[pos_i * N + pos_j - 1]["node_val"] == Empty:
        untake.append(pos_i * N + pos_j - 1)
    if pos_i < N - 1 and net.nodes[(pos_i + 1) * N + pos_j]["node_val"] == Empty:
        untake.append((pos_i + 1) * N + pos_j)
    if pos_j < N - 1 and net.nodes[pos_i * N + pos_j + 1]["node_val"] == Empty:
        untake.append(pos_i * N + pos_j + 1)
    return untake


def _be_blocked(net: nx.Graph, pos: int, N: int) -> bool:
    free_space = 0
    up_pos = pos - N
    down_pos = pos + N
    left_pos = pos - 1
    right_pos = pos + 1
    if up_pos >= 0 and net.nodes[up_pos]["node_val"] == Empty:
        free_space += 1
    if down_pos <= N * N - 1 and net.nodes[down_pos]["node_val"] == Empty:
        free_space += 1
    if left_pos % N != N - 1 and net.nodes[left_pos]["node_val"] == Empty:
        free_space += 1
    if right_pos % N != 0 and net.nodes[right_pos]["node_val"] == Empty:
        free_space += 1
    return free_space < 2


def _is_isolated(net: nx.Graph, pos: int, N: int) -> bool:
    flag = True
    up_pos = pos - N
    down_pos = pos + N
    left_pos = pos - 1
    right_pos = pos + 1
    if up_pos >= 0 and net[pos][up_pos]["color"] == "red":
        flag = False
    if down_pos <= N * N - 1 and net[pos][down_pos]["color"] == "red":
        flag = False
    if left_pos % N != N - 1 and net[pos][left_pos]["color"] == "red":
        flag = False
    if right_pos % N != 0 and net[pos][right_pos]["color"] == "red":
        flag = False
    return flag


class _SearchNode:
    def __init__(self, net: nx.Graph, path: list, allocated_incomplete_nodes: list, N: int) -> None:
        self.net = net.copy()
        self.path = path.copy()
        self.f = 0
        self.free_space: set = set()
        for pnode in path:
            for nnode in _count_pos_untake(net, pnode, N):
                self.free_space.add(nnode)
        self.f = len(self.free_space)

    def __lt__(self, other: "_SearchNode") -> bool:
        return self.f > other.f


def _find_pre_pos(path: list, pos: int, N: int) -> int:
    pos_i = pos // N
    pos_j = pos % N
    if pos_i > 0 and (pos_i - 1) * N + pos_j in path:
        return (pos_i - 1) * N + pos_j
    if pos_j > 0 and pos_i * N + pos_j - 1 in path:
        return pos_i * N + pos_j - 1
    if pos_i < N - 1 and (pos_i + 1) * N + pos_j in path:
        return (pos_i + 1) * N + pos_j
    if pos_j < N - 1 and pos_i * N + pos_j + 1 in path:
        return pos_i * N + pos_j + 1
    return -1


def _create_net(allocated_incomplete_nodes: dict, N: int) -> nx.Graph:
    net = nx.Graph()
    for i in range(N):
        for j in range(N):
            if i * N + j not in allocated_incomplete_nodes:
                net.add_node(i * N + j, pos=(j, i), node_val=Empty, node_color="lightgray")
            else:
                net.add_node(i * N + j, pos=(j, i), node_val=allocated_incomplete_nodes[i * N + j], node_color="black")
    for i in range(N):
        for j in range(N):
            if i < N - 1:
                net.add_edge(i * N + j, (i + 1) * N + j, color="lightgray")
            if j > 0:
                net.add_edge(i * N + j, i * N + j - 1, color="lightgray")
    return net


def _one_layer_map_route(
    origin_graph: nx.Graph,
    pre_layer_incomplete_nodes: dict,
    dgraph: nx.DiGraph,
    allocated_nodes_cache: dict,
    graph_nodes_pos: dict,
    layer_index: int,
    N: int,
    required_life_time: int,
    max_measure_delay: int,
) -> tuple:
    incomplete_nodes_allocated_size = 0
    graph = origin_graph.copy()
    net = _create_net(pre_layer_incomplete_nodes, N)
    allocated_nodes: dict = {}
    for key in pre_layer_incomplete_nodes:
        allocated_nodes[pre_layer_incomplete_nodes[key]] = key
        if len(list(graph.neighbors(pre_layer_incomplete_nodes[key]))):
            incomplete_nodes_allocated_size += 1

    for _ in range(Round):
        current_nodes_to_map = []

        parent_values: set = set()
        for gnode in graph.nodes():
            parent_values.add(graph.nodes[gnode]["parent"])

        dgraph_nodes = list(dgraph.nodes()).copy()
        for dnode in dgraph_nodes:
            if dnode not in parent_values:
                for snode in list(dgraph.successors(dnode)).copy():
                    dgraph.remove_edge(dnode, snode)
                dgraph.remove_node(dnode)

        avail_parent: set = set()
        cur_layer_parent: set = set()
        for dnode in dgraph.nodes():
            if len(list(dgraph.predecessors(dnode))) == 0:
                cur_layer_parent.add(dnode)
        copy_cur_layer_parent = cur_layer_parent.copy()
        avail_parent |= copy_cur_layer_parent

        for _ in range(Average_Depth):
            cur_layer_parent = set()
            for parent in copy_cur_layer_parent:
                for suc_parent in dgraph.successors(parent):
                    cur_layer_parent.add(suc_parent)
            copy_cur_layer_parent = cur_layer_parent.copy()
            avail_parent |= copy_cur_layer_parent

        nodes_index = 0
        for anode in allocated_nodes:
            current_nodes_to_map.append(anode)
            nodes_index += 1

        for gnode in graph.nodes():
            if (
                graph.nodes[gnode]["parent"] in avail_parent
                and gnode not in allocated_nodes_cache
                and gnode not in current_nodes_to_map
                and nodes_index <= N * N * 12
            ):
                current_nodes_to_map.append(gnode)
                nodes_index += 1

        current_graph_to_map = nx.subgraph(graph, current_nodes_to_map).copy()
        components = list(nx.connected_components(current_graph_to_map))

        for component in components:
            if len(list(component)) == 1:
                continue

            allocated_incomplete_nodes_list = [
                cnode
                for cnode in list(component)
                if cnode in allocated_nodes and len(list(graph.neighbors(cnode)))
            ]

            if not allocated_incomplete_nodes_list:
                begin_node = list(component)[0]
                allocated_incomplete_nodes_list = [begin_node]
                incomplete_nodes_allocated_size += 1
                empty_nnodes = [n for n in net.nodes() if net.nodes[n]["node_val"] == Empty]
                if not empty_nnodes:
                    continue
                chosen_pos = empty_nnodes[random.randint(0, len(empty_nnodes) - 1)]
                allocated_nodes[begin_node] = chosen_pos
                net.nodes[chosen_pos]["node_val"] = begin_node
                net.nodes[chosen_pos]["node_color"] = "blue"

            while allocated_incomplete_nodes_list:
                allocated_incomplete_node = allocated_incomplete_nodes_list[0]
                allocated_incomplete_nodes_list.remove(allocated_incomplete_node)

                if not len(list(graph.neighbors(allocated_incomplete_node))):
                    graph.remove_node(allocated_incomplete_node)
                    if allocated_incomplete_node in graph_nodes_pos:
                        max_measure_delay = max(max_measure_delay, layer_index - graph_nodes_pos[allocated_incomplete_node])
                    current_graph_to_map.remove_node(allocated_incomplete_node)
                    continue

                neigh_nodes = list(current_graph_to_map.neighbors(allocated_incomplete_node)).copy()
                allocated_neigh_nodes = []
                unallocated_neigh_nodes = []
                for neigh_node in neigh_nodes:
                    if neigh_node in current_nodes_to_map:
                        if neigh_node in allocated_nodes:
                            allocated_neigh_nodes.append(neigh_node)
                        else:
                            unallocated_neigh_nodes.append(neigh_node)

                for allocated_neigh_node in allocated_neigh_nodes:
                    src_pos = allocated_nodes[allocated_incomplete_node]
                    target_pos = allocated_nodes[allocated_neigh_node]
                    node_set = [src_pos, target_pos] + [n for n in net.nodes() if net.nodes[n]["node_val"] == Empty]
                    route_net = nx.subgraph(net, node_set)
                    if nx.has_path(route_net, src_pos, target_pos):
                        simple_path = nx.shortest_path(route_net, src_pos, target_pos)
                        pre_node = src_pos
                        for snode in simple_path[1:]:
                            if snode != target_pos:
                                net.nodes[snode]["node_val"] = Auxiliary
                            net[pre_node][snode]["color"] = "red"
                            pre_node = snode
                        graph.remove_edge(allocated_incomplete_node, allocated_neigh_node)
                        current_graph_to_map.remove_edge(allocated_incomplete_node, allocated_neigh_node)
                        if not len(list(graph.neighbors(allocated_neigh_node))):
                            graph.remove_node(allocated_neigh_node)
                            if allocated_neigh_node in graph_nodes_pos:
                                max_measure_delay = max(max_measure_delay, layer_index - graph_nodes_pos[allocated_neigh_node])
                            current_graph_to_map.remove_node(allocated_neigh_node)
                            if allocated_neigh_node in allocated_incomplete_nodes_list:
                                allocated_incomplete_nodes_list.remove(allocated_neigh_node)
                            incomplete_nodes_allocated_size -= 1

                search_set: list = []
                search_index = 0
                search_node = _SearchNode(net.copy(), [allocated_nodes[allocated_incomplete_node]], allocated_incomplete_nodes_list, N)
                heapq.heappush(search_set, search_node)
                while search_set:
                    search_node = heapq.heappop(search_set)
                    if search_node.f >= len(unallocated_neigh_nodes):
                        break
                    if search_index > SearchUpperBound:
                        print("reach search upper bound break")
                        break
                    search_index += 1
                    if search_node.f > 0:
                        search_net = search_node.net
                        search_path = search_node.path
                        for untake_pos in _count_pos_untake(search_net, search_path[-1], N):
                            new_net = search_net.copy()
                            new_net.add_edge(search_path[-1], untake_pos)
                            new_path = search_path.copy()
                            new_path.append(untake_pos)
                            new_net.nodes[untake_pos]["node_val"] = Auxiliary
                            heapq.heappush(search_set, _SearchNode(new_net, new_path, allocated_incomplete_nodes_list, N))

                if search_node.f:
                    net = search_node.net.copy()
                    path = search_node.path.copy()
                    free_pos_set = search_node.free_space.copy()

                    pre_node = allocated_nodes[allocated_incomplete_node]
                    for pnode in path[1:]:
                        net[pre_node][pnode]["color"] = "red"
                        pre_node = pnode

                    for free_pos in free_pos_set:
                        if not unallocated_neigh_nodes:
                            break
                        pre_pos = _find_pre_pos(path, free_pos, N)
                        if pre_pos == -1:
                            continue
                        unallocated_neigh_node = unallocated_neigh_nodes[0]
                        unallocated_neigh_nodes.remove(unallocated_neigh_node)
                        net.nodes[free_pos]["node_val"] = unallocated_neigh_node
                        net.nodes[free_pos]["node_color"] = "blue"
                        net[pre_pos][free_pos]["color"] = "red"
                        allocated_nodes[unallocated_neigh_node] = free_pos
                        graph.remove_edge(allocated_incomplete_node, unallocated_neigh_node)
                        current_graph_to_map.remove_edge(allocated_incomplete_node, unallocated_neigh_node)
                        if len(list(graph.neighbors(unallocated_neigh_node))):
                            allocated_incomplete_nodes_list.append(unallocated_neigh_node)
                            incomplete_nodes_allocated_size += 1

                if not len(list(graph.neighbors(allocated_incomplete_node))):
                    incomplete_nodes_allocated_size -= 1

                allocated_incomplete_nodes_list.sort(key=lambda n: len(list(graph.neighbors(n))), reverse=True)

        for nnode in net.nodes():
            if net.nodes[nnode]["node_val"] != Empty and net.nodes[nnode]["node_val"] != Auxiliary:
                if _is_isolated(net, nnode, N) and nnode not in pre_layer_incomplete_nodes:
                    del allocated_nodes[net.nodes[nnode]["node_val"]]
                    net.nodes[nnode]["node_val"] = Empty
                    net.nodes[nnode]["node_color"] = "lightgray"

    all_nodes = list(graph.nodes()).copy()
    for gnode in all_nodes:
        if not len(list(graph.neighbors(gnode))):
            graph.remove_node(gnode)
            if gnode in graph_nodes_pos:
                max_measure_delay = max(max_measure_delay, layer_index - graph_nodes_pos[gnode])

    allocated_nodes_incomplete: dict = {}
    inter_edges = []
    for allocated_node in allocated_nodes:
        if allocated_node in graph.nodes():
            neigh_allocated_nodes = list(graph.neighbors(allocated_node))
            if (
                len(neigh_allocated_nodes) == 1
                and neigh_allocated_nodes[0] not in allocated_nodes
                and neigh_allocated_nodes[0] not in allocated_nodes_cache
            ):
                allocated_nodes_incomplete[allocated_nodes[allocated_node]] = neigh_allocated_nodes[0]
                graph_nodes_pos[neigh_allocated_nodes[0]] = layer_index
                graph.remove_edge(allocated_node, neigh_allocated_nodes[0])
                graph.remove_node(allocated_node)
                if allocated_node in graph_nodes_pos:
                    max_measure_delay = max(max_measure_delay, layer_index - graph_nodes_pos[allocated_node])
            else:
                allocated_nodes_incomplete[allocated_nodes[allocated_node]] = allocated_node
        if allocated_node in pre_layer_incomplete_nodes.values():
            if allocated_node in graph_nodes_pos:
                required_life_time = max(required_life_time, layer_index - graph_nodes_pos[allocated_node])
            inter_edges.append((allocated_nodes[allocated_node], graph_nodes_pos[allocated_node], layer_index))

    for nnode in net.nodes():
        if net.nodes[nnode]["node_val"]:
            graph_nodes_pos[net.nodes[nnode]["node_val"]] = layer_index

    return net, allocated_nodes_incomplete, graph, graph_nodes_pos, inter_edges, required_life_time, max_measure_delay


def _refresh(
    allocated_nodes_cache_origin: dict,
    graph_nodes_pos: dict,
    layer_index: int,
    N: int,
    required_life_time: int,
) -> tuple:
    refresh_index = 0
    refresh_inter_edges_list = []
    refresh_net_list = []
    allocated_nodes_cache = allocated_nodes_cache_origin.copy()
    allocated_keys = list(allocated_nodes_cache.keys())
    while allocated_keys:
        refresh_index += 1
        inter_edges = []
        net = _create_net({}, N)
        for akey in allocated_keys:
            akey_pos = allocated_nodes_cache[akey]
            if net.nodes[akey_pos]["node_val"] == Empty:
                net.nodes[akey_pos]["node_val"] = akey
                del allocated_nodes_cache[akey]
                inter_edges.append((akey_pos, graph_nodes_pos[akey], layer_index))
                if akey in graph_nodes_pos:
                    required_life_time = max(required_life_time, layer_index - graph_nodes_pos[akey])
                graph_nodes_pos[akey] = layer_index
        refresh_inter_edges_list.append(inter_edges)
        refresh_net_list.append(net)
        layer_index += 1
        allocated_keys = list(allocated_nodes_cache.keys())
    print("refresh", refresh_index)
    return layer_index, refresh_net_list, graph_nodes_pos, refresh_inter_edges_list, required_life_time


def map_route(
    graph: nx.Graph,
    dgraph: nx.DiGraph,
    NQubit: int,
    N: int,
    Refresh: bool,
    RefreshBound: int,
) -> tuple:
    """Map and route a graph state onto an N×N 2D grid.

    Returns:
        (net_list, layer_index, layer_list, left_graph_nodes_list,
         inter_edges_list, refresh_begin_list, refresh_end_list,
         required_life_time, max_measure_delay)

    layer_index == Empty (1e1000) indicates a timeout.
    """
    required_life_time = 0
    refresh_begin_list: list = []
    refresh_end_list: list = []

    P = 0.05
    layer_index = 0
    refresh_index = 0

    net_list: list = []
    inter_edges_list: list = []
    layer_list: list = []
    graph_nodes_pos: dict = {}
    left_graph_nodes_list: list = []

    allocated_nodes_cache: dict = {}
    allocated_incomplete_nodes: dict = {}
    max_measure_delay = 0

    while len(graph.nodes()):
        exit_flag = all(
            edge[0] in allocated_nodes_cache
            and edge[1] in allocated_nodes_cache
            and allocated_nodes_cache[edge[0]] == allocated_nodes_cache[edge[1]]
            for edge in graph.edges()
        )
        if exit_flag:
            break

        left_graph_nodes_list.append(len(graph.nodes()))
        layer_list.append(layer_index)

        akeys = list(allocated_nodes_cache.keys())
        for gnode in akeys:
            if gnode not in graph.nodes() or not len(list(graph.neighbors(gnode))):
                del allocated_nodes_cache[gnode]

        allocated_incomplete_nodes.clear()
        index = 0
        keys = list(allocated_nodes_cache.keys()).copy()
        while keys:
            if index >= N * N * P:
                break
            key = keys[0]
            keys.remove(key)
            if allocated_nodes_cache[key] not in allocated_incomplete_nodes:
                flag = False
                for kkey in keys:
                    if (
                        graph.has_edge(key, kkey)
                        and allocated_nodes_cache[kkey] not in allocated_incomplete_nodes
                    ):
                        allocated_incomplete_nodes[allocated_nodes_cache[kkey]] = kkey
                        del allocated_nodes_cache[kkey]
                        keys.remove(kkey)
                        index += 1
                        flag = True
                if flag:
                    allocated_incomplete_nodes[allocated_nodes_cache[key]] = key
                    del allocated_nodes_cache[key]
                    index += 1

        keys = list(allocated_nodes_cache.keys()).copy()
        while keys:
            if index >= N * N * P:
                break
            key = keys[0]
            keys.remove(key)
            if allocated_nodes_cache[key] not in allocated_incomplete_nodes:
                allocated_incomplete_nodes[allocated_nodes_cache[key]] = key
                del allocated_nodes_cache[key]
                index += 1

        (
            net,
            allocated_incomplete_nodes,
            graph,
            graph_nodes_pos,
            inter_edges,
            required_life_time,
            max_measure_delay,
        ) = _one_layer_map_route(
            graph,
            allocated_incomplete_nodes,
            dgraph,
            allocated_nodes_cache,
            graph_nodes_pos,
            layer_index,
            N,
            required_life_time,
            max_measure_delay,
        )
        net_list.append(net)
        inter_edges_list.append(inter_edges)

        for apos in allocated_incomplete_nodes:
            allocated_nodes_cache[allocated_incomplete_nodes[apos]] = apos

        print(len(list(graph.nodes())))
        layer_index += 1
        refresh_index += 1

        if refresh_index >= RefreshBound and Refresh:
            refresh_begin_list.append(layer_index)
            (
                layer_index,
                refresh_net_list,
                graph_nodes_pos,
                refresh_inter_edges_list,
                required_life_time,
            ) = _refresh(allocated_nodes_cache, graph_nodes_pos, layer_index, N, required_life_time)
            refresh_end_list.append(layer_index)
            net_list += refresh_net_list
            inter_edges_list += refresh_inter_edges_list
            refresh_index = 0

        if NQubit == 36 and N == 6 and layer_index > 10000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay
        if NQubit == 64 and layer_index > 10000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay
        if layer_index > 20000:
            return net_list, Empty, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay

    return net_list, layer_index, layer_list, left_graph_nodes_list, inter_edges_list, refresh_begin_list, refresh_end_list, required_life_time, max_measure_delay
