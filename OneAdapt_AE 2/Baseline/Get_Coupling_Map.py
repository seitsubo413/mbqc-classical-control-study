import networkx as nx

def get_coupling_map(row, col, draw=False):
    G = nx.grid_2d_graph(row, col)

    positions = {(x, y): (y, -x) for (x, y) in G.nodes()}
    nx.set_node_attributes(G, positions, name='position')
        
    G = nx.relabel_nodes(G, {(x, y): i for i, (x, y) in enumerate(G.nodes())})
    coupling_map = list(G.edges)

    if draw:
        pos = nx.get_node_attributes(G, 'position')
        nx.draw(G, pos, with_labels=True, node_size=500, node_color='lightblue', font_size=10, font_color='black')
    
    return coupling_map