import networkx as nx

def signal_shift(graph):
    idx = 1
    while idx:
        idx = 0
        for nnode in graph.nodes():
            successors = list(graph.successors(nnode))
            for snode in successors:
                # the phase is clifford
                if graph.nodes[snode]['phase'] % 2 == 0 and graph.nodes[snode]['node_val'] != 'IO' and  graph.nodes[snode]['node_val'] != 'Out':
                    successors_snode = list(graph.successors(snode))
                    for ssnode in successors_snode:
                        if (nnode, ssnode) not in graph.edges():
                            graph.add_edge(nnode, ssnode)
                    graph.remove_edge(nnode, snode)
                    idx += 1
    return graph

def determine_dependency(graph):
    # initialize the determined graph
    determined_graph = nx.DiGraph()

    # add basic nodes in graph to the determined graph with its positon and phase information
    for nnode in graph.nodes():
        determined_graph.add_node(nnode, pos = graph.nodes[nnode]['pos'], phase = graph.nodes[nnode]['phase'], node_val = graph.nodes[nnode]['node_val'])
    
    for nnode in graph.nodes():
        for snode in graph.successors(nnode):
            # judge whether it is a directed edge
            if snode not in graph.predecessors(nnode):
                determined_graph.add_edge(nnode, snode)

                for ssnode in graph.successors(snode):
                    if ssnode in graph.predecessors(snode):
                        determined_graph.add_edge(nnode, ssnode)

    
    # perform signal shift
    reverse_G = determined_graph.reverse(copy=True)
    reverse_order = list(nx.topological_sort(reverse_G))
    topo_order = reverse_order[::-1]
    strict_graph = determined_graph.copy()
    measure_determined_graph = signal_shift(determined_graph)
    

    return strict_graph, graph