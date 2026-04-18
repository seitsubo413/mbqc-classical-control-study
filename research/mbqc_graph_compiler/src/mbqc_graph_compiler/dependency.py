"""
Feedforward dependency extraction and signal shift optimization for MBQC.

determine_dependency: extracts X/Z dependency edges from a graph state.
signal_shift: rewrites Z dependencies to reduce feedforward chain depth.
"""
from __future__ import annotations

import networkx as nx


def _reduce_redundancy(graph: nx.DiGraph, gs: nx.DiGraph) -> tuple[nx.DiGraph, nx.DiGraph]:
    for nnode in graph.nodes():
        if graph.nodes[nnode]["phase"] == 0:
            succ_nodes = list(graph.successors(nnode)).copy()
            for snode in succ_nodes:
                if graph[nnode][snode]["dependency"] == "x":
                    graph.remove_edge(nnode, snode)
        elif graph.nodes[nnode]["phase"] == 2:
            for snode in graph.successors(nnode):
                if graph[nnode][snode]["dependency"] == "x":
                    graph[nnode][snode]["dependency"] = "z"
    return graph.copy(), gs


def signal_shift(graph: nx.DiGraph, gs: nx.DiGraph) -> tuple[nx.DiGraph, nx.DiGraph]:
    """Shift Z dependencies forward to reduce feedforward chain depth (D_ff)."""
    zgraph = nx.DiGraph()
    for nnode in graph.nodes():
        zgraph.add_node(nnode, pos=graph.nodes[nnode]["pos"])

    for edge in graph.edges():
        if graph[edge[0]][edge[1]]["dependency"] == "z":
            zgraph.add_edge(edge[0], edge[1])

    while True:
        shift_z_edges = [
            zedge
            for zedge in zgraph.edges()
            if len(list(zgraph.predecessors(zedge[0]))) == 0
            and len(list(graph.successors(zedge[1]))) != 0
        ]

        if not shift_z_edges:
            break

        for sze in shift_z_edges:
            head_node = sze[0]
            tail_node = sze[1]
            neigh_tail_nodes = list(graph.successors(tail_node)).copy()
            for ntn in neigh_tail_nodes:
                if graph[tail_node][ntn]["dependency"] == "z":
                    if not (graph.has_edge(head_node, ntn) and graph[head_node][ntn]["dependency"] == "z"):
                        graph.add_edge(head_node, ntn)
                        graph[head_node][ntn]["dependency"] = "z"
                        zgraph.add_edge(head_node, ntn)
                elif graph[tail_node][ntn]["dependency"] == "x":
                    if not (graph.has_edge(head_node, ntn) and graph[head_node][ntn]["dependency"] == "x"):
                        graph.add_edge(head_node, ntn)
                        graph[head_node][ntn]["dependency"] = "x"
            graph.remove_edge(sze[0], sze[1])
            zgraph.remove_edge(sze[0], sze[1])

    print("shift signal finished")
    return graph, gs


def determine_dependency(graph: nx.DiGraph) -> tuple[nx.DiGraph, nx.DiGraph]:
    """Extract X/Z feedforward dependency graph from a graph state.

    Returns:
        (dependency_graph, graph_state_with_dependency)
        dependency_graph: DiGraph with edge attribute 'dependency' in {'x', 'z'}.
    """
    determined_graph = nx.DiGraph()

    for nnode in graph.nodes():
        determined_graph.add_node(
            nnode,
            pos=graph.nodes[nnode]["pos"],
            phase=graph.nodes[nnode]["phase"],
        )

    for nnode in graph.nodes():
        for snode in graph.successors(nnode):
            if snode not in graph.predecessors(nnode):
                determined_graph.add_edge(nnode, snode)
                determined_graph[nnode][snode]["dependency"] = "x"

                for ssnode in graph.successors(snode):
                    determined_graph.add_edge(nnode, ssnode)
                    determined_graph[nnode][ssnode]["dependency"] = "z"

    determined_graph, graph = _reduce_redundancy(determined_graph, graph)
    return determined_graph, graph
