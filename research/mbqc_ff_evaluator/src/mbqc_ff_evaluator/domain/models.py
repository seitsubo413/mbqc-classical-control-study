from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Final

from .enums import Algorithm, ArtifactStatus, DependencyKind, ReferenceKind

IQR_QUANTILES: Final[tuple[float, float]] = (0.25, 0.75)


@dataclass(frozen=True)
class ExperimentConfig:
    algorithm: Algorithm
    hardware_size: int
    logical_qubits: int
    seed: int
    refresh: bool
    refresh_bound: int


@dataclass(frozen=True)
class FFNode:
    node_id: int
    phase: float | None
    node_type: str


@dataclass(frozen=True)
class FFEdge:
    src: int
    dst: int
    dependency: DependencyKind


@dataclass(frozen=True)
class DependencyGraphSnapshot:
    nodes: tuple[FFNode, ...]
    edges: tuple[FFEdge, ...]
    chain_depth: int


@dataclass(frozen=True)
class DepthReference:
    kind: ReferenceKind
    depth: int


@dataclass(frozen=True)
class OnePercArtifact:
    config: ExperimentConfig
    status: ArtifactStatus
    layer_index: float
    required_lifetime_layers: int | None
    max_measure_delay_layers: int | None
    dgraph_num_nodes: int
    dgraph_num_edges: int
    ff_nodes: tuple[FFNode, ...]
    ff_edges: tuple[FFEdge, ...]
    ff_chain_depth_raw: int
    ff_chain_depth_shifted: int | None
    depth_reference: DepthReference | None
    elapsed_sec: float
    shifted_dependency_graph: DependencyGraphSnapshot | None = None


@dataclass(frozen=True)
class DependencyBudget:
    dependency_depth: int
    photon_lifetime_us: float
    t_ff_cond_ns: float


@dataclass(frozen=True)
class LayerBudget:
    layer_metric: int
    photon_lifetime_us: float
    per_layer_budget_ns: float


@dataclass(frozen=True)
class ConservativeBudget:
    dependency_budget_ns: float
    hold_budget_ns: float
    meas_budget_ns: float
    t_cons_ns: float


@dataclass(frozen=True)
class NumericSummary:
    count: int
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float
    mean: float


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_path: Path
    artifact: OnePercArtifact


def build_numeric_summary(values: tuple[float, ...]) -> NumericSummary:
    if not values:
        raise ValueError("values must not be empty")

    ordered = tuple(sorted(values))
    lower_half = ordered[: len(ordered) // 2]
    upper_half = ordered[(len(ordered) + 1) // 2 :]
    q1 = median(lower_half) if lower_half else ordered[0]
    q3 = median(upper_half) if upper_half else ordered[-1]
    mean = sum(ordered) / len(ordered)
    return NumericSummary(
        count=len(ordered),
        minimum=ordered[0],
        q1=float(q1),
        median=float(median(ordered)),
        q3=float(q3),
        maximum=ordered[-1],
        mean=mean,
    )
