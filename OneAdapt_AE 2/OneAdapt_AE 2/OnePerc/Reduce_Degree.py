Max_Degree = 4

def reduce_degree(graph):

    all_nodes = list(graph.nodes()).copy()
    nodes_size = len(all_nodes) + 1
    for gnode in all_nodes:
        graph.nodes[gnode]['parent'] = gnode

    for gnode in all_nodes:
        neigh_gnodes = list(graph.neighbors(gnode)).copy()

        if len(neigh_gnodes) > Max_Degree:
            for i in range(Max_Degree - 1):
                neigh_gnode = neigh_gnodes[0]
                neigh_gnodes.remove(neigh_gnode)

            for neigh_gnode in neigh_gnodes:
                graph.remove_edge(gnode, neigh_gnode)

            pre_node = gnode
            while len(neigh_gnodes):
                added_node = nodes_size
                nodes_size += 1
                graph.add_node(added_node)
                graph.nodes[added_node]['qubit'] = graph.nodes[gnode]['qubit']
                graph.nodes[added_node]['parent'] = gnode
                graph.add_edge(pre_node, added_node)
                
                if len(neigh_gnodes) < Max_Degree:
                    added_edges_bound = Max_Degree - 1
                else:
                    added_edges_bound = Max_Degree - 2 
                for i in range(added_edges_bound):
                    if len(neigh_gnodes) == 0:
                        break
                    neigh_gnode = neigh_gnodes[0]
                    graph.add_edge(added_node, neigh_gnode)
                    neigh_gnodes.remove(neigh_gnode)
                pre_node = added_node

    return graph