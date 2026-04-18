"""
Reduces graph state node degree to at most 4 for physical layout constraints.
"""
from __future__ import annotations

import networkx as nx

MAX_DEGREE = 4


def reduce_degree(graph: nx.Graph) -> nx.Graph:
    """Reduce all node degrees to at most MAX_DEGREE by inserting auxiliary nodes."""
    all_nodes = list(graph.nodes()).copy()
    nodes_size = len(all_nodes) + 1

    for gnode in all_nodes:
        graph.nodes[gnode]["parent"] = gnode

    for gnode in all_nodes:
        neigh_gnodes = list(graph.neighbors(gnode)).copy()

        if len(neigh_gnodes) > MAX_DEGREE:
            for _ in range(MAX_DEGREE - 1):
                neigh_gnode = neigh_gnodes[0]
                neigh_gnodes.remove(neigh_gnode)

            for neigh_gnode in neigh_gnodes:
                graph.remove_edge(gnode, neigh_gnode)

            pre_node = gnode
            while neigh_gnodes:
                added_node = nodes_size
                nodes_size += 1
                graph.add_node(added_node)
                graph.nodes[added_node]["qubit"] = graph.nodes[gnode]["qubit"]
                graph.nodes[added_node]["parent"] = gnode
                graph.add_edge(pre_node, added_node)

                if len(neigh_gnodes) < MAX_DEGREE:
                    added_edges_bound = MAX_DEGREE - 1
                else:
                    added_edges_bound = MAX_DEGREE - 2
                for _ in range(added_edges_bound):
                    if not neigh_gnodes:
                        break
                    neigh_gnode = neigh_gnodes[0]
                    graph.add_edge(added_node, neigh_gnode)
                    neigh_gnodes.remove(neigh_gnode)
                pre_node = added_node

    return graph
