import networkx as nx

def reduce_redundancy(graph, gs):
    for nnode in graph.nodes():
        # the phase is 0
        if graph.nodes[nnode]['phase'] == 0:
            succ_nodes = list(graph.successors(nnode)).copy()
            for snode in succ_nodes:
                if graph[nnode][snode]['dependency'] == 'x':
                    graph.remove_edge(nnode, snode)
        # the phase is pi // 2
        elif graph.nodes[nnode]['phase'] == 2:
            for snode in graph.successors(nnode):
                if graph[nnode][snode]['dependency'] == 'x':
                    graph[nnode][snode]['dependency'] = 'z'      
    return graph.copy(), gs

def signal_shift(graph, gs):

    input_nodes = []
    output_nodes = []

    # determine the input and output nodes
    for nnode in graph.nodes():
        if len(list(graph.predecessors(nnode))) == 0:
            input_nodes.append(nnode)
        if len(list(graph.successors(nnode))) == 0:
            output_nodes.append(nnode)

    zgraph = nx.DiGraph()
    for nnode in graph.nodes():
        zgraph.add_node(nnode, pos = graph.nodes[nnode]['pos'])
    
    for edge in graph.edges():
        if graph[edge[0]][edge[1]]['dependency'] == 'z':
            zgraph.add_edge(edge[0], edge[1])   
    
    while 1:
        shift_z_edges = []
        for zedge in zgraph.edges():
            if len(list(zgraph.predecessors(zedge[0]))) == 0 and len(list(graph.successors(zedge[1]))) != 0:
                shift_z_edges.append(zedge)
        
        if len(shift_z_edges) == 0:
            break

        for sze in shift_z_edges:
            head_node = sze[0]
            tail_node = sze[1]
            neigh_tail_nodes = list(graph.successors(tail_node)).copy()
            for ntn in neigh_tail_nodes:
                if graph[tail_node][ntn]['dependency'] == 'z':
                    if not (graph.has_edge(head_node, ntn) and graph[head_node][ntn]['dependency'] == 'z'):
                        graph.add_edge(head_node, ntn)
                        graph[head_node][ntn]['dependency'] = 'z'
                        zgraph.add_edge(head_node, ntn)

                elif graph[tail_node][ntn]['dependency'] == 'x':
                    if not (graph.has_edge(head_node, ntn) and graph[head_node][ntn]['dependency'] == 'x'):
                        graph.add_edge(head_node, ntn)
                        graph[head_node][ntn]['dependency'] = 'x'
            graph.remove_edge(sze[0], sze[1])
            zgraph.remove_edge(sze[0], sze[1])

    print ("shift signal finished")    
    return graph, gs

def determine_dependency(graph):
    # initialize the determined graph
    determined_graph = nx.DiGraph()

    # add basic nodes in graph to the determined graph with its positon and phase information
    for nnode in graph.nodes():
        determined_graph.add_node(nnode, pos = graph.nodes[nnode]['pos'], phase = graph.nodes[nnode]['phase'])
    
    for nnode in graph.nodes():
        for snode in graph.successors(nnode):
            # judge whether it is a directed edge
            if snode not in graph.predecessors(nnode):
                # propogate one x dependency to neighbor
                determined_graph.add_edge(nnode, snode)
                determined_graph[nnode][snode]['dependency'] = 'x'

                # propogate one z dependency to successor's neighbor
                for ssnode in graph.successors(snode):
                    determined_graph.add_edge(nnode, ssnode)
                    determined_graph[nnode][ssnode]['dependency'] = 'z'

    # reduce redundancy in special case
    determined_graph, graph = reduce_redundancy(determined_graph, graph)
    # perform signal shift
    # determined_graph, graph = signal_shift(determined_graph, graph)
    return determined_graph, graph