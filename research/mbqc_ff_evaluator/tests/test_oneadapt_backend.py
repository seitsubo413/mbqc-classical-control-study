from __future__ import annotations

import pytest

from mbqc_ff_evaluator.adapters.oneadapt_backend import OneAdaptBackend
from mbqc_ff_evaluator.adapters.oneadapt_circuit_factory import OneAdaptCircuitPayload
from mbqc_ff_evaluator.domain.circuit_models import CircuitProgram
from mbqc_ff_evaluator.domain.errors import DependencyGraphError


class FakeGraph:
    def __init__(
        self,
        *,
        nodes: tuple[tuple[int, dict[str, object]], ...],
        edges: tuple[tuple[int, int, dict[str, object]], ...],
    ) -> None:
        self._nodes = nodes
        self._edges = edges

    def nodes(self, data: bool = False) -> tuple[tuple[int, dict[str, object]], ...]:
        assert data is True
        return self._nodes

    def edges(self, data: bool = False) -> tuple[tuple[int, int, dict[str, object]], ...]:
        assert data is True
        return self._edges

    def copy(self) -> FakeGraph:
        return FakeGraph(nodes=self._nodes, edges=self._edges)


def test_extract_dependency_graphs_allows_signal_shift_failure() -> None:
    backend = object.__new__(OneAdaptBackend)
    raw_graph = FakeGraph(
        nodes=((1, {"node_type": "M"}), (2, {"node_type": "M"})),
        edges=((1, 2, {"dependency": "x"}),),
    )
    payload = OneAdaptCircuitPayload(
        logical_qubits=2,
        raw_gates=(),
        program=CircuitProgram(logical_qubits=2, operations=()),
    )

    extraction = backend._extract_dependency_graphs(
        payload=payload,
        determine_dependency=lambda graph_state: (raw_graph, graph_state),
        signal_shift=_raise_runtime_error,
        generate_graph_state=lambda raw_gates, logical_qubits: raw_graph,
    )

    assert extraction.raw_snapshot.chain_depth == 1
    assert extraction.shifted_snapshot is None
    assert extraction.shifted_unavailable_reason == "RuntimeError: signal_shift unavailable"


def test_extract_dependency_graphs_propagates_shifted_graph_errors() -> None:
    backend = object.__new__(OneAdaptBackend)
    raw_graph = FakeGraph(
        nodes=((1, {"node_type": "M"}), (2, {"node_type": "M"})),
        edges=((1, 2, {"dependency": "x"}),),
    )
    invalid_shifted_graph = FakeGraph(
        nodes=((1, {"node_type": "M"}), (2, {"node_type": "M"})),
        edges=((1, 2, {"dependency": "bad"}),),
    )
    payload = OneAdaptCircuitPayload(
        logical_qubits=2,
        raw_gates=(),
        program=CircuitProgram(logical_qubits=2, operations=()),
    )

    with pytest.raises(DependencyGraphError, match="unknown dependency kind"):
        backend._extract_dependency_graphs(
            payload=payload,
            determine_dependency=lambda graph_state: (raw_graph, graph_state),
            signal_shift=lambda dgraph, graph_state: (invalid_shifted_graph, graph_state),
            generate_graph_state=lambda raw_gates, logical_qubits: raw_graph,
        )


def _raise_runtime_error(dgraph: object, graph_state: object) -> tuple[object, object]:
    _ = dgraph, graph_state
    raise RuntimeError("signal_shift unavailable")
