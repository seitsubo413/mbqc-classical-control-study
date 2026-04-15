import networkx as nx

def draw_net(net, cross_nodes):
    pos = nx.get_node_attributes(net, 'pos')
    for u, v, data in net.edges(data=True):
            if net[u][v]['avail']:
                nx.draw_networkx_edges(net, pos, edgelist=[(u, v)], edge_color='green', alpha=0.7)
            nx.draw_networkx_edges(net, pos, edgelist=[(u, v)], edge_color=net[u][v]['color'], alpha=0.7)

    node_size = []
    labels = {}
    for node in net.nodes():
        if node in cross_nodes.keys():
            node_size.append(30)
            labels[node] = str(cross_nodes[node])
        else:
            node_size.append(5)
            labels[node] = ''
    nx.draw_networkx_nodes(net, pos = pos, node_size = node_size)
    nx.draw_networkx_labels(net, pos = pos, labels=labels, font_size=6, font_color='black', font_family='sans-serif')

    return