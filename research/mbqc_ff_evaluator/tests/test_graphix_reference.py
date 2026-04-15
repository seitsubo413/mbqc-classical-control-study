from __future__ import annotations

import pytest

from mbqc_ff_evaluator.adapters.graphix_reference import GraphixReferenceBackend
from mbqc_ff_evaluator.domain.circuit_models import CZOperation, CircuitProgram, JOperation
from mbqc_ff_evaluator.domain.enums import Algorithm, ReferenceKind
from mbqc_ff_evaluator.domain.models import ExperimentConfig


class FakeCircuitFactory:
    def build_program(self, config: ExperimentConfig) -> CircuitProgram:
        assert config.algorithm is Algorithm.QAOA
        return CircuitProgram(
            logical_qubits=2,
            operations=(
                JOperation(qubit=0, phase_quarter_turns=0.0),
                JOperation(qubit=1, phase_quarter_turns=0.0),
                CZOperation(qubit_a=0, qubit_b=1),
            ),
        )


@pytest.mark.graphix
def test_graphix_reference_backend_returns_independent_depth() -> None:
    backend = GraphixReferenceBackend(circuit_factory=FakeCircuitFactory())
    config = ExperimentConfig(
        algorithm=Algorithm.QAOA,
        hardware_size=4,
        logical_qubits=2,
        seed=0,
        refresh=True,
        refresh_bound=20,
    )

    depth_reference = backend.compute_reference(config)

    assert depth_reference is not None
    assert depth_reference.kind is ReferenceKind.INDEPENDENT_COMPILER
    assert depth_reference.depth >= 1
