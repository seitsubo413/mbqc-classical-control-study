import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


from benchmarks.generate_qec_benchmark import *
from qiskit import transpile
from qiskit.converters import circuit_to_dag

depth_list_origin = {}
Alg_list = ['QFT', 'QSim', 'Grover']
D = 20
MF = 15
for a in Alg_list:
    depth_list_origin[a] = []
    for N in range(6, 61, 6):
        RL = N * 3

        if a == 'QFT':
            circ_origin = qec_qft(N)
        elif a == 'QSim':
            circ_origin = qec_qsim(N)
        else:
            circ_origin = qec_grover(N)

        circ = transpile(
            circ_origin,
            basis_gates=["cx", "h", "s", "t"], 
            optimization_level = 1
        )

        dag = circuit_to_dag(circ)
        avail_pre_qubits = []
        qubit_life_time = {}
        for i in range(N):
            qubit_life_time[i] = 0

        cur_qubit = 0
        depth = 0
        mg_index = 0
        mg_layer = 0
        mg_begin = False
        ancilla_begin = False
        pending_qubit = -1
        
        pending_node = -1
        real_depth = 0
        ready_flag = {}
        for i in range(N):
            ready_flag[i] = 0
        # RL = N * 2
        # print(RL)
        while dag.depth():
            # if depth % MF == 0:
            #     mg_index = NM
            if mg_layer == MF:
                mg_index +=1
                mg_layer = 0
            
            if mg_index > 1:
                mg_begin = False


            cur_qubit = -1
            for q in qubit_life_time:
                if qubit_life_time[q] == RL:
                    cur_qubit = q
                    qubit_life_time[q] = 0
                    break
            
            front_layer = dag.front_layer()
            if cur_qubit != -1:   
                # print("forced refresh") 
                for node in front_layer:
                    if node.op.num_qubits == 1:
                        if node.qargs[0]._index == cur_qubit:
                            if pending_qubit == -1:
                                pending_qubit = cur_qubit
                                pending_node = node
                                # print("qubit", pending_qubit)
                            
                            if node.op._name != 't':
                                if ready_flag[cur_qubit] >= D:
                                    dag.remove_op_node(node)
                                    ready_flag[cur_qubit] -= D
                                    pending_qubit = -1
                                    pending_node = -1
                            else:
                                if mg_index:
                                    if ready_flag[cur_qubit] >= D:
                                        dag.remove_op_node(node)
                                        mg_index -= 1
                                        ready_flag[cur_qubit] -= D
                                        pending_qubit = -1
                                        pending_node = -1
                                else:
                                    mg_begin = True
                    else:
                        q0 = node.qargs[0]._index
                        q1 = node.qargs[1]._index
                        if q0 == cur_qubit:
                            if pending_qubit == -1:
                                pending_qubit = cur_qubit
                                pending_node = node
                                # print("qubit", pending_qubit)
                            if ready_flag[q0] >= D:
                                if q1 in avail_pre_qubits:
                                    dag.remove_op_node(node)
                                    avail_pre_qubits.remove(q1)
                                    ready_flag[q0] -= D
                                    pending_qubit = -1
                                    pending_node = -1
                        elif q1 == cur_qubit:
                            if pending_qubit == -1:
                                pending_qubit = cur_qubit
                                pending_node = node
                            if ready_flag[q1] >= D:
                                if q0 in avail_pre_qubits:
                                    dag.remove_op_node(node)
                                    avail_pre_qubits.remove(q0)
                                    ready_flag[q1] -= D
                                    pending_qubit = -1
                                    pending_node = -1
                avail_pre_qubits.append(cur_qubit)

            else:

                # print("qubit", pending_qubit, pending_node)
                if pending_qubit != -1:
                    # print("status", ready_flag[pending_qubit], pending_node.op._name)
                    # print(mg_begin)
                    if mg_begin:
                        if real_depth % 3  == 1:
                            ready_flag[pending_qubit] += 1
                            for q in qubit_life_time:
                                qubit_life_time[q] += 1
                            real_depth += 1
                            continue
                    else:
                        if real_depth % 2  == 0:
                            ready_flag[pending_qubit] += 1
                            for q in qubit_life_time:
                                qubit_life_time[q] += 1
                            # print("pass")
                            real_depth += 1
                            continue 
                if mg_begin:
                    if pending_qubit == -1:
                        if real_depth % 2 == 0:
                            mg_layer += 1
                            for q in qubit_life_time:
                                qubit_life_time[q] += 1
                            real_depth += 1
                            continue
                    else:
                        if real_depth % 3 == 0:
                            mg_layer += 1
                            for q in qubit_life_time:
                                qubit_life_time[q] += 1
                            real_depth += 1
                            continue

                # print("execute")
                cur_node = -1
                other_qubit = -1
                if pending_node == -1:
                    
                    for node in front_layer:
                        if node.op.num_qubits == 2:
                            # print("two-qubit refresh")
                            q0 = node.qargs[0]._index
                            q1 = node.qargs[1]._index
                            if q0 in avail_pre_qubits:
                                if cur_qubit == -1:
                                    cur_qubit = q1
                                    cur_node = node
                                    other_qubit = q0
                                elif qubit_life_time[cur_qubit] < qubit_life_time[q1]:
                                    cur_qubit = q1
                                    cur_node = node    
                                    other_qubit = q0                    
                            if q1 in avail_pre_qubits:
                                if cur_qubit == -1:
                                    cur_qubit = q0
                                    cur_node = node
                                    other_qubit = q1
                                elif qubit_life_time[cur_qubit] < qubit_life_time[q0]:
                                    cur_qubit = q0
                                    cur_node = node
                                    other_qubit = q1
                    # print(cur_qubit)
                else:
                    # print("select")
                    cur_qubit = pending_qubit
                    cur_node = pending_node
                
                # print(cur_node)
                if cur_node != -1:
                    
                    # print("single-qubit refresh")
                    if pending_qubit == -1:
                        pending_qubit = cur_qubit 
                        pending_node = cur_node
                        # print("qubit", pending_qubit)
                    # print("here", cur_qubit)
                    if ready_flag[cur_qubit] >= D:
                        dag.remove_op_node(cur_node)
                        if other_qubit in avail_pre_qubits:
                            avail_pre_qubits.remove(other_qubit)
                        avail_pre_qubits.append(cur_qubit)
                        qubit_life_time[cur_qubit] = 0
                        ready_flag[cur_qubit] -= D
                        pending_qubit = -1
                        pending_node = -1

                else:
                    # print("just refresh") 
                    if pending_qubit == -1:
                        for node in front_layer:
                            if node.op.num_qubits == 1:
                                q0 = node.qargs[0]._index
                                if node.op._name != 't' or mg_index:

                                    if cur_qubit == -1:
                                        cur_qubit = q0
                                        cur_node = node
                                    elif qubit_life_time[cur_qubit] < qubit_life_time[q0]:
                                        cur_qubit = q0
                                        cur_node = node 
                                        
                                
                                else:
                                    mg_begin = True
                    else:
                        cur_qubit = pending_qubit
                        cur_node = pending_node
                    # print("single gate", cur_node)
                    if cur_node != -1:
                        
                        if pending_qubit == -1:
                            pending_qubit = cur_qubit
                            pending_node = cur_node
                            # print("qubit", pending_qubit)
                        if ready_flag[cur_qubit] >= D:
                            dag.remove_op_node(cur_node)
                            avail_pre_qubits.append(cur_qubit)
                            qubit_life_time[cur_qubit] = 0
                            ready_flag[cur_qubit] -= D
                            pending_qubit = -1
                            pending_node = -1
                            if cur_node.op._name == 't':
                                mg_index -= 1 
                    else:
                        for node in front_layer:
                            if cur_qubit == -1 or qubit_life_time[cur_qubit] < qubit_life_time[q0]:
                                cur_qubit = q0
                                cur_node = node  
                        avail_pre_qubits.append(cur_qubit) 
                        qubit_life_time[cur_qubit] = 0 
                real_depth += 1             
            for q in qubit_life_time:
                qubit_life_time[q] += 1
            depth += 1
            if depth >= 10 ** 6:
                break   
            
        depth_list_origin[a].append(depth)
        print(depth)
with open("data/qec_depth_us.txt", 'w') as file:
    file.write(str(depth_list_origin) + '\n')
