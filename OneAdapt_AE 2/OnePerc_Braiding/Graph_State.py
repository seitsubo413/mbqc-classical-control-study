import pyzx as zx
import networkx as nx

# using pyzx to help draw cz j circuit, assume xphase to be j phase
def show_circuit(qubits, gates_list):
    c = zx.Circuit(qubit_amount=qubits)
    for gate in gates_list:
        if gate.type() == "J":
            c.add_gate("XPhase", gate.qubit, phase = gate.phase / 4)
        else:
            c.add_gate("CZ", gate.qubit1, gate.qubit2)
    zx.draw(c)
    return

# use to directed edges to represent one undirected edge
def add_undirected_edge(graph, node1, node2):
    graph.add_edge(node1, node2)
    graph.add_edge(node2, node1)
    return graph

# turn circuit into graph_state according to the gate list
def generate_graph_state(gates_list, qubits):
    node_index = 1
    pos_x = 0
    pre_nodes = {}
    pre_gate = {}

    # -1 indicate no gate implemented on that qubit
    for q in range(qubits):
        pre_nodes[q] = -1
        pre_gate[q] = 'CZ'

    # initialize the graph
    graph = nx.DiGraph()

    for gate in gates_list:
        # gate type is J
        if gate.type() == "J":
            qubit = gate.qubit
            if pre_nodes[gate.qubit] == -1:
                graph.add_node(node_index, node_val = "In", pos = (pos_x, - qubit), phase = gate.phase, qubit = qubit)
                graph.add_node(node_index + 1, node_val = "Out", pos  = (pos_x + 3, - qubit), phase = -1, qubit = qubit)
                graph.add_edge(node_index, node_index + 1)

                qubit = gate.qubit
                pre_nodes[qubit] = node_index + 1
                pos_x += 6
                node_index += 2
            else:
                pre_node = pre_nodes[gate.qubit]
                if graph.nodes[pre_node]['node_val'] == "Out":
                    graph.nodes[pre_node]['node_val'] = "Aux"
                else:
                    graph.nodes[pre_node]['node_val'] = "In"
                qubit = gate.qubit
                graph.add_node(node_index, node_val = "Out", pos = (pos_x, - qubit), phase = -1, qubit = qubit)

                graph.nodes[pre_node]['phase'] = gate.phase
                graph.add_edge(pre_node, node_index)
                pre_nodes[qubit] = node_index
                pos_x += 3
                node_index += 1
            pre_gate[qubit] = 'J'
        # gate type is CZ
        elif gate.type() == "CZ":
            qubit1 = gate.qubit1
            qubit2 = gate.qubit2
            if pre_nodes[qubit1] == -1:
                graph.add_node(node_index, node_val = "IO", pos = (pos_x, - qubit1), phase = -1, qubit = qubit1)
                pre_nodes[qubit1] = node_index
                node_q1 = node_index
                pos_x += 3
                node_index += 1
            else:
                node_q1 = pre_nodes[qubit1]
            
            if pre_nodes[qubit2] == -1:
                graph.add_node(node_index, node_val = "IO", pos = (pos_x, - qubit2), phase = -1, qubit = qubit2)
                pre_nodes[qubit2] = node_index
                node_q2 = node_index
                pos_x += 3
                node_index += 1
            else:
                node_q2 = pre_nodes[qubit2]
            pre_gate[qubit1] = 'CZ'
            pre_gate[qubit2] = 'CZ'
            graph = add_undirected_edge(graph, node_q1, node_q2)
            
    return graph
