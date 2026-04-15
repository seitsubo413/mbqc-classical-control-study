import random

def random_result(prob):
    random_value = random.random()
    return random_value < prob

def percolate_intra_layer(net, time_index, N, P):
    for i in range(N):
        for j in range(N):
            net.add_node(time_index * N * N + i * N + j, pos = (j, i))
    for i in range(N):
        for j in range(N):
            if i > 0:
                if random_result(P):
                    net.add_edge(time_index * N * N + i * N + j, time_index * N * N + (i - 1) * N + j)
                    net[time_index * N * N + i * N + j][time_index * N * N + (i - 1) * N + j]['color'] = 'lightgray'
                    net[time_index * N * N + i * N + j][time_index * N * N + (i - 1) * N + j]['avail'] = True
            if j > 0:
                if random_result(P):
                    net.add_edge(time_index * N * N + i * N + j, time_index * N * N + i * N + j - 1)
                    net[time_index * N * N + i * N + j][time_index * N * N + i * N + j - 1]['color'] = 'lightgray'
                    net[time_index * N * N + i * N + j][time_index * N * N + i * N + j - 1]['avail'] = True
    return net

def percolate_inter_layer(net, time_index, N, P):
    for i in range(N):
        for j in range(N):
            if random_result(P):
                net.add_edge(time_index * N * N + i * N + j, (time_index + 1) * N * N + i * N + j)
                net[time_index * N * N + i * N + j][(time_index + 1) * N * N + i * N + j]['color'] = 'lightgray'
                net[time_index * N * N + i * N + j][(time_index + 1) * N * N + i * N + j]['avail'] = True
    return net