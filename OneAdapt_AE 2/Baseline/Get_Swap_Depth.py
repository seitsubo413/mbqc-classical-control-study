def get_swap_depths(transpiled_circuit):
    qubit_depths = {}
    swap_gate_depths_qubits = {}

    for qubit in transpiled_circuit.qubits:
        qubit_depths[qubit] = 0

    pre_gate = 'cz'
    for j, instr in enumerate(transpiled_circuit.data):
        pre_gate = instr[0].name
        if instr[0].name == 'swap':
            if max(qubit_depths[instr[1][0]], qubit_depths[instr[1][1]]) not in swap_gate_depths_qubits.keys():
                swap_gate_depths_qubits[max(qubit_depths[instr[1][0]], qubit_depths[instr[1][1]])] = [(int(str(instr[1][0]).split(',')[-1][0:-1]), int(str(instr[1][1]).split(',')[-1][0:-1]))]
            else:
                swap_gate_depths_qubits[max(qubit_depths[instr[1][0]], qubit_depths[instr[1][1]])].append((int(str(instr[1][0]).split(',')[-1][0:-1]), int(str(instr[1][1]).split(',')[-1][0:-1])))
        if instr[0].num_qubits == 1:
            if instr[0].name == 'h':
                qubit_depths[instr[1][0]] += 1
            else:
                if pre_gate != 'h':
                    qubit_depths[instr[1][0]] += 2
            # else:
            #     qubit_depths[instr[1][0]] += 2
        else:
            if instr[0].name == 'cz':
                qubit_depths[instr[1][0]] = max(qubit_depths[instr[1][0]], qubit_depths[instr[1][1]]) + 3
            else:
                qubit_depths[instr[1][0]] = max(qubit_depths[instr[1][0]], qubit_depths[instr[1][1]]) + 1
            qubit_depths[instr[1][1]] = qubit_depths[instr[1][0]]
    return swap_gate_depths_qubits, qubit_depths

def get_depths(transpiled_circuit):
    qubit_depths = {}

    for qubit in transpiled_circuit.qubits:
        qubit_depths[qubit] = 0

    pre_gate = 'cz'
    for j, instr in enumerate(transpiled_circuit.data):
        pre_gate = instr[0].name
        if instr[0].num_qubits == 1:
            if instr[0].name == 'h':
                qubit_depths[instr[1][0]] += 1
            else:
                if pre_gate != 'h':
                    qubit_depths[instr[1][0]] += 2
            # else:
            #     qubit_depths[instr[1][0]] += 2
        else:
            # print(instr)
            if instr[0].name == 'cz':
                qubit_depths[instr[1][0]] = max(qubit_depths[instr[1][0]], qubit_depths[instr[1][1]]) + 3
            else:
                qubit_depths[instr[1][0]] = max(qubit_depths[instr[1][0]], qubit_depths[instr[1][1]]) + 1
            qubit_depths[instr[1][1]] = qubit_depths[instr[1][0]]
    return qubit_depths