from __future__ import annotations

import math
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from typing import Any, Iterator

import networkx

from mbqc_graph_compiler import (
    Empty,
    determine_dependency,
    generate_graph_state,
    map_route,
    reduce_degree,
    signal_shift,
)
from mbqc_ff_evaluator.adapters.oneadapt_circuit_factory import OneAdaptCircuitFactory
from mbqc_ff_evaluator.domain.enums import ArtifactStatus, DependencyKind
from mbqc_ff_evaluator.domain.errors import DependencyGraphError
from mbqc_ff_evaluator.domain.models import (
    DependencyGraphSnapshot,
    ExperimentConfig,
    FFEdge,
    FFNode,
    OnePercArtifact,
)
from mbqc_ff_evaluator.ports.compiler_backend import CompilerBackend
from mbqc_ff_evaluator.services.compute_metrics import compute_ff_chain_depth_raw, compute_ff_chain_depth_shifted


@dataclass(frozen=True)
class DependencyExtraction:
    dgraph_raw: Any
    graph_state_with_dependency: Any
    raw_snapshot: DependencyGraphSnapshot
    shifted_snapshot: DependencyGraphSnapshot | None
    shifted_unavailable_reason: str | None


class OneAdaptBackend(CompilerBackend):
    """Adapter using mbqc_graph_compiler for graph state compilation."""

    def __init__(
        self,
        oneadapt_root: Any = None,  # kept for API compatibility, no longer used
        *,
        verbose: bool = False,
        circuit_factory: OneAdaptCircuitFactory | None = None,
    ) -> None:
        self._verbose = verbose
        self._circuit_factory = circuit_factory or OneAdaptCircuitFactory()

    def collect_artifact(self, config: ExperimentConfig) -> OnePercArtifact:
        start = time.perf_counter()
        with self._external_output_context():
            extraction = self._extract_dependency_graphs(
                payload=self._circuit_factory.build_payload(config),
                generate_graph_state=generate_graph_state,
                determine_dependency=determine_dependency,
                signal_shift=signal_shift,
            )

            undirected_graph_state = networkx.Graph(extraction.graph_state_with_dependency)
            reduced_graph_state = reduce_degree(undirected_graph_state)

            (
                _net_list,
                layer_index,
                _layer_list,
                _left_graph_nodes_list,
                _inter_edges_list,
                _refresh_begin_list,
                _refresh_end_list,
                required_life_time,
                max_measure_delay,
            ) = map_route(
                reduced_graph_state,
                extraction.dgraph_raw.copy(),
                config.logical_qubits,
                config.hardware_size,
                config.refresh,
                config.refresh_bound,
            )

        layer_index_value = float(layer_index)
        status = ArtifactStatus.TIMEOUT_GUARD if self._is_timeout_guard(layer_index_value) else ArtifactStatus.SUCCESS
        elapsed_sec = time.perf_counter() - start

        return OnePercArtifact(
            config=config,
            status=status,
            layer_index=layer_index_value,
            required_lifetime_layers=self._coerce_optional_int(required_life_time),
            max_measure_delay_layers=self._coerce_optional_int(max_measure_delay),
            dgraph_num_nodes=int(extraction.dgraph_raw.number_of_nodes()),
            dgraph_num_edges=int(extraction.dgraph_raw.number_of_edges()),
            ff_nodes=extraction.raw_snapshot.nodes,
            ff_edges=extraction.raw_snapshot.edges,
            ff_chain_depth_raw=extraction.raw_snapshot.chain_depth,
            ff_chain_depth_shifted=(
                None if extraction.shifted_snapshot is None else extraction.shifted_snapshot.chain_depth
            ),
            depth_reference=None,
            elapsed_sec=elapsed_sec,
            shifted_dependency_graph=extraction.shifted_snapshot,
            shifted_unavailable_reason=extraction.shifted_unavailable_reason,
        )

    def collect_dependency_snapshots(
        self,
        config: ExperimentConfig,
    ) -> tuple[DependencyGraphSnapshot, DependencyGraphSnapshot | None]:
        with self._external_output_context():
            extraction = self._extract_dependency_graphs(
                payload=self._circuit_factory.build_payload(config),
                generate_graph_state=generate_graph_state,
                determine_dependency=determine_dependency,
                signal_shift=signal_shift,
            )
        return extraction.raw_snapshot, extraction.shifted_snapshot

    def _extract_dependency_graphs(
        self,
        *,
        payload: Any,
        generate_graph_state: Any,
        determine_dependency: Any,
        signal_shift: Any,
    ) -> DependencyExtraction:
        graph_state = generate_graph_state(payload.raw_gates, payload.logical_qubits)
        dgraph_raw, graph_state_with_dependency = determine_dependency(graph_state)

        raw_snapshot = self._build_snapshot(dgraph_raw, shifted=False)

        try:
            dgraph_shifted, _ = signal_shift(dgraph_raw.copy(), graph_state_with_dependency.copy())
        except Exception as exc:
            shifted_snapshot = None
            shifted_unavailable_reason = self._format_exc(exc)
        else:
            shifted_snapshot = self._build_snapshot(dgraph_shifted, shifted=True)
            shifted_unavailable_reason = None

        return DependencyExtraction(
            dgraph_raw=dgraph_raw,
            graph_state_with_dependency=graph_state_with_dependency,
            raw_snapshot=raw_snapshot,
            shifted_snapshot=shifted_snapshot,
            shifted_unavailable_reason=shifted_unavailable_reason,
        )

    def _build_snapshot(self, dgraph: Any, *, shifted: bool) -> DependencyGraphSnapshot:
        nodes = self._build_ff_nodes(dgraph)
        edges = self._build_ff_edges(dgraph)
        if shifted:
            chain_depth = compute_ff_chain_depth_shifted(
                tuple(n.node_id for n in nodes), edges
            )
        else:
            chain_depth = compute_ff_chain_depth_raw(
                tuple(n.node_id for n in nodes), edges
            )
        return DependencyGraphSnapshot(nodes=nodes, edges=edges, chain_depth=chain_depth)

    def _build_ff_nodes(self, dgraph: Any) -> tuple[FFNode, ...]:
        nodes: list[FFNode] = []
        for node_id, attrs in dgraph.nodes(data=True):
            phase_raw = attrs.get("phase")
            phase = None if phase_raw == -1 else float(phase_raw) if phase_raw is not None else None
            nodes.append(
                FFNode(
                    node_id=int(node_id),
                    phase=phase,
                    node_type=str(attrs.get("node_val", attrs.get("node_type", "Unknown"))),
                )
            )
        return tuple(nodes)

    def _build_ff_edges(self, dgraph: Any) -> tuple[FFEdge, ...]:
        edges: list[FFEdge] = []
        for src, dst, attrs in dgraph.edges(data=True):
            dependency_raw = attrs.get("dependency")
            if dependency_raw == DependencyKind.X.value:
                dependency = DependencyKind.X
            elif dependency_raw == DependencyKind.Z.value:
                dependency = DependencyKind.Z
            else:
                raise DependencyGraphError(f"unknown dependency kind: {dependency_raw}")
            edges.append(FFEdge(src=int(src), dst=int(dst), dependency=dependency))
        return tuple(edges)

    def _is_timeout_guard(self, layer_index: float) -> bool:
        return layer_index == Empty or math.isinf(layer_index)

    def _coerce_optional_int(self, value: Any) -> int | None:
        if isinstance(value, float) and (value == Empty or math.isinf(value)):
            return None
        return int(value)

    def _format_exc(self, exc: Exception) -> str:
        message = str(exc).strip()
        return f"{type(exc).__name__}: {message}" if message else type(exc).__name__

    @contextmanager
    def _external_output_context(self) -> Iterator[None]:
        if self._verbose:
            yield
            return
        sink = StringIO()
        with redirect_stdout(sink), redirect_stderr(sink):
            yield
