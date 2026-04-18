"""
Converts a JCZ gate list into an MBQC graph state (directed NetworkX graph).

Node attributes: node_val ("In" | "Out" | "Aux" | "IO"), pos, phase, qubit
Directed edges represent the flow structure of the graph state.
"""
from __future__ import annotations

import networkx as nx


def _add_undirected_edge(graph: nx.DiGraph, node1: int, node2: int) -> nx.DiGraph:
    graph.add_edge(node1, node2)
    graph.add_edge(node2, node1)
    return graph


def generate_graph_state(gates_list: list, qubits: int) -> nx.DiGraph:
    """Convert a JCZ circuit into an MBQC graph state.

    Args:
        gates_list: List of JGate and CZGate objects.
        qubits: Number of logical qubits.

    Returns:
        Directed NetworkX graph representing the graph state.
        Node attributes: node_val, pos, phase, qubit.
    """
    node_index = 1
    pos_x = 0
    pre_nodes: dict[int, int] = {}
    pre_gate: dict[int, str] = {}

    for q in range(qubits):
        pre_nodes[q] = -1
        pre_gate[q] = "CZ"

    graph = nx.DiGraph()

    for gate in gates_list:
        if gate.type() == "J":
            qubit = gate.qubit
            if pre_nodes[qubit] == -1:
                graph.add_node(node_index, node_val="In", pos=(pos_x, -qubit), phase=gate.phase, qubit=qubit)
                graph.add_node(node_index + 1, node_val="Out", pos=(pos_x + 3, -qubit), phase=-1, qubit=qubit)
                graph.add_edge(node_index, node_index + 1)
                pre_nodes[qubit] = node_index + 1
                pos_x += 6
                node_index += 2
            else:
                pre_node = pre_nodes[qubit]
                if graph.nodes[pre_node]["node_val"] == "Out":
                    graph.nodes[pre_node]["node_val"] = "Aux"
                else:
                    graph.nodes[pre_node]["node_val"] = "In"
                graph.add_node(node_index, node_val="Out", pos=(pos_x, -qubit), phase=-1, qubit=qubit)
                graph.nodes[pre_node]["phase"] = gate.phase
                graph.add_edge(pre_node, node_index)
                pre_nodes[qubit] = node_index
                pos_x += 3
                node_index += 1
            pre_gate[qubit] = "J"

        elif gate.type() == "CZ":
            qubit1 = gate.qubit1
            qubit2 = gate.qubit2
            if pre_nodes[qubit1] == -1:
                graph.add_node(node_index, node_val="IO", pos=(pos_x, -qubit1), phase=-1, qubit=qubit1)
                pre_nodes[qubit1] = node_index
                node_q1 = node_index
                pos_x += 3
                node_index += 1
            else:
                node_q1 = pre_nodes[qubit1]

            if pre_nodes[qubit2] == -1:
                graph.add_node(node_index, node_val="IO", pos=(pos_x, -qubit2), phase=-1, qubit=qubit2)
                pre_nodes[qubit2] = node_index
                node_q2 = node_index
                pos_x += 3
                node_index += 1
            else:
                node_q2 = pre_nodes[qubit2]

            pre_gate[qubit1] = "CZ"
            pre_gate[qubit2] = "CZ"
            graph = _add_undirected_edge(graph, node_q1, node_q2)

    return graph
