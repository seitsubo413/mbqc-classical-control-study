from __future__ import annotations

import pytest

from mbqc_ff_evaluator.adapters.graphix_translation import extract_graphix_gflow_depth
from mbqc_ff_evaluator.domain.circuit_models import CZOperation, CircuitProgram, JOperation


@pytest.mark.graphix
def test_extract_graphix_gflow_depth_for_simple_program() -> None:
    program = CircuitProgram(
        logical_qubits=2,
        operations=(
            JOperation(qubit=0, phase_quarter_turns=0.0),
            JOperation(qubit=1, phase_quarter_turns=0.0),
            CZOperation(qubit_a=0, qubit_b=1),
        ),
    )

    depth = extract_graphix_gflow_depth(program)

    assert depth >= 1
