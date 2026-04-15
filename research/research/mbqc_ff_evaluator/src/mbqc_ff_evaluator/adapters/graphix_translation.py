from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from mbqc_ff_evaluator.domain.circuit_models import CZOperation, CircuitProgram, JOperation


def build_graphix_circuit(program: CircuitProgram) -> Any:
    """Translate the shared JCZ program into a graphix Circuit.

    OneAdapt's `J(α)` convention satisfies:
    - `J(0) = H`
    - `J(α) J(0) = Rz(α)`
    Therefore the equivalent graphix expansion is `Rz(α) -> H`.
    """

    from graphix import Circuit

    circuit = Circuit(program.logical_qubits)
    for operation in program.operations:
        if isinstance(operation, JOperation):
            circuit.rz(operation.qubit, operation.phase_quarter_turns * math.pi / 4.0)
            circuit.h(operation.qubit)
            continue
        if isinstance(operation, CZOperation):
            circuit.cz(operation.qubit_a, operation.qubit_b)
            continue
        raise TypeError(f"unsupported circuit operation: {type(operation)!r}")
    return circuit


def extract_graphix_gflow_depth(program: CircuitProgram) -> int:
    """Return the measurement depth implied by graphix gflow layers."""

    circuit = build_graphix_circuit(program)
    transpile_result = circuit.transpile()
    pattern = transpile_result.pattern.to_bloch()
    gflow = pattern.extract_gflow()
    return _measurement_depth(gflow.partial_order_layers, tuple(pattern.output_nodes))


def _measurement_depth(
    partial_order_layers: Sequence[frozenset[int]],
    output_nodes: Sequence[int],
) -> int:
    if not partial_order_layers:
        return 0
    output_layer = frozenset(output_nodes)
    if output_layer and partial_order_layers[0] == output_layer:
        return max(len(partial_order_layers) - 1, 0)
    return len(partial_order_layers)
