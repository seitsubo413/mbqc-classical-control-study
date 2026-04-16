from __future__ import annotations

import importlib
import math
import os
import sys
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any, Iterator

from mbqc_ff_evaluator.domain.enums import ArtifactStatus, DependencyKind
from mbqc_ff_evaluator.domain.errors import DependencyGraphError
from mbqc_ff_evaluator.domain.models import (
    DependencyGraphSnapshot,
    ExperimentConfig,
    FFEdge,
    FFNode,
    OnePercArtifact,
)
from mbqc_ff_evaluator.adapters.oneadapt_circuit_factory import OneAdaptCircuitFactory, OneAdaptCircuitPayload
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
    """Adapter around OneAdapt / OnePerc."""

    def __init__(
        self,
        oneadapt_root: Path | None = None,
        *,
        verbose: bool = False,
        circuit_factory: OneAdaptCircuitFactory | None = None,
    ) -> None:
        self._repo_root = Path(__file__).resolve().parents[5]
        self._oneadapt_root = oneadapt_root or self._repo_root / "OneAdapt_AE 2"
        self._verbose = verbose
        if not self._oneadapt_root.exists():
            raise FileNotFoundError(f"OneAdapt root not found: {self._oneadapt_root}")
        self._circuit_factory = circuit_factory or OneAdaptCircuitFactory(self._oneadapt_root)
        self._ensure_import_path()
        self._ensure_matplotlib_cache_dir()

    def collect_artifact(self, config: ExperimentConfig) -> OnePercArtifact:
        self._ensure_import_path()
        start = time.perf_counter()
        with self._external_output_context():
            networkx_module = importlib.import_module("networkx")

            graph_state_module = importlib.import_module("OnePerc.Graph_State")
            dependency_module = importlib.import_module("OnePerc.Determine_Dependency")
            reduce_degree_module = importlib.import_module("OnePerc.Reduce_Degree")
            map_route_module = importlib.import_module("OnePerc.Mapping_Routing_origin")

            payload = self._circuit_factory.build_payload(config)
            generate_graph_state = getattr(graph_state_module, "generate_graph_state")
            determine_dependency = getattr(dependency_module, "determine_dependency")
            signal_shift = getattr(dependency_module, "signal_shift")
            reduce_degree = getattr(reduce_degree_module, "reduce_degree")
            map_route = getattr(map_route_module, "map_route")
            empty_value = getattr(map_route_module, "Empty")

            extraction = self._extract_dependency_graphs(
                payload=payload,
                determine_dependency=determine_dependency,
                signal_shift=signal_shift,
                generate_graph_state=generate_graph_state,
            )

            undirected_graph_state = networkx_module.Graph(extraction.graph_state_with_dependency)
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
        status = ArtifactStatus.TIMEOUT_GUARD if self._is_timeout_guard(layer_index_value, empty_value) else ArtifactStatus.SUCCESS
        elapsed_sec = time.perf_counter() - start

        return OnePercArtifact(
            config=config,
            status=status,
            layer_index=layer_index_value,
            required_lifetime_layers=self._coerce_optional_int(required_life_time, empty_value),
            max_measure_delay_layers=self._coerce_optional_int(max_measure_delay, empty_value),
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
        self._ensure_import_path()
        with self._external_output_context():
            graph_state_module = importlib.import_module("OnePerc.Graph_State")
            dependency_module = importlib.import_module("OnePerc.Determine_Dependency")

            payload = self._circuit_factory.build_payload(config)
            generate_graph_state = getattr(graph_state_module, "generate_graph_state")
            determine_dependency = getattr(dependency_module, "determine_dependency")
            signal_shift = getattr(dependency_module, "signal_shift")
            extraction = self._extract_dependency_graphs(
                payload=payload,
                determine_dependency=determine_dependency,
                signal_shift=signal_shift,
                generate_graph_state=generate_graph_state,
            )
        return extraction.raw_snapshot, extraction.shifted_snapshot

    def _ensure_import_path(self) -> None:
        oneadapt_path = str(self._oneadapt_root)
        if oneadapt_path not in sys.path:
            sys.path.insert(0, oneadapt_path)

    def _ensure_matplotlib_cache_dir(self) -> None:
        cache_dir = self._repo_root / "research" / "mbqc_ff_evaluator" / ".cache" / "matplotlib"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))

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

    def _extract_dependency_graphs(
        self,
        *,
        payload: OneAdaptCircuitPayload,
        determine_dependency: Any,
        signal_shift: Any,
        generate_graph_state: Any,
    ) -> DependencyExtraction:
        graph_state = generate_graph_state(payload.raw_gates, payload.logical_qubits)
        dgraph_raw, graph_state_with_dependency = determine_dependency(graph_state)

        raw_nodes = self._build_ff_nodes(dgraph_raw)
        raw_edges = self._build_ff_edges(dgraph_raw)
        raw_depth = compute_ff_chain_depth_raw(
            tuple(node.node_id for node in raw_nodes),
            raw_edges,
        )
        raw_snapshot = DependencyGraphSnapshot(
            nodes=raw_nodes,
            edges=raw_edges,
            chain_depth=raw_depth,
        )

        try:
            shifted_result = signal_shift(dgraph_raw.copy(), graph_state_with_dependency.copy())
        except Exception as exc:
            shifted_snapshot = None
            shifted_unavailable_reason = self._format_shifted_unavailable_reason(exc)
        else:
            dgraph_shifted, _ = shifted_result
            shifted_snapshot = self._build_shifted_snapshot(dgraph_shifted)
            shifted_unavailable_reason = None

        return DependencyExtraction(
            dgraph_raw=dgraph_raw,
            graph_state_with_dependency=graph_state_with_dependency,
            raw_snapshot=raw_snapshot,
            shifted_snapshot=shifted_snapshot,
            shifted_unavailable_reason=shifted_unavailable_reason,
        )

    def _build_shifted_snapshot(self, dgraph_shifted: Any) -> DependencyGraphSnapshot:
        shifted_nodes = self._build_ff_nodes(dgraph_shifted)
        shifted_edges = self._build_ff_edges(dgraph_shifted)
        shifted_depth = compute_ff_chain_depth_shifted(
            tuple(node.node_id for node in shifted_nodes),
            shifted_edges,
        )
        return DependencyGraphSnapshot(
            nodes=shifted_nodes,
            edges=shifted_edges,
            chain_depth=shifted_depth,
        )

    def _format_shifted_unavailable_reason(self, exc: Exception) -> str:
        message = str(exc).strip()
        if not message:
            return type(exc).__name__
        return f"{type(exc).__name__}: {message}"

    def _is_timeout_guard(self, layer_index: float, empty_value: object) -> bool:
        if layer_index == empty_value:
            return True
        return math.isinf(layer_index)

    def _coerce_optional_int(self, value: Any, empty_value: object) -> int | None:
        if value == empty_value:
            return None
        if isinstance(value, float) and math.isinf(value):
            return None
        return int(value)

    @contextmanager
    def _external_output_context(self) -> Iterator[None]:
        if self._verbose:
            yield
            return
        sink = StringIO()
        with redirect_stdout(sink), redirect_stderr(sink):
            yield
