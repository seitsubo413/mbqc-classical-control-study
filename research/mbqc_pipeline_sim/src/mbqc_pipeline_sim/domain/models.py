from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from .enums import DagVariant, ReleaseMode, SchedulingPolicy


@dataclass(frozen=True)
class PipelineConfig:
    issue_width: int = 1
    l_meas: int = 1
    l_ff: int = 1
    meas_width: int | None = None
    ff_width: int | None = None
    release_mode: ReleaseMode = ReleaseMode.SAME_CYCLE
    policy: SchedulingPolicy = SchedulingPolicy.ASAP
    seed: int = 0

    def __post_init__(self) -> None:
        if self.issue_width <= 0:
            raise ValueError("issue_width must be positive")
        if self.l_meas <= 0 or self.l_ff <= 0:
            raise ValueError("latencies must be positive")
        if self.meas_width is not None and self.meas_width <= 0:
            raise ValueError("meas_width must be positive when provided")
        if self.ff_width is not None and self.ff_width <= 0:
            raise ValueError("ff_width must be positive when provided")


@dataclass(frozen=True)
class MeasNode:
    node_id: int
    phase: float | None
    node_type: str


@dataclass(frozen=True)
class MeasEdge:
    src: int
    dst: int
    dependency: str


@dataclass
class SimDAG:
    """Pre-processed dependency DAG ready for simulation."""

    nodes: tuple[MeasNode, ...]
    edges: tuple[MeasEdge, ...]
    adjacency: dict[int, list[int]] = field(default_factory=dict)
    reverse_adj: dict[int, list[int]] = field(default_factory=dict)
    indegree: dict[int, int] = field(default_factory=dict)
    topo_level: dict[int, int] = field(default_factory=dict)
    remaining_depth: dict[int, int] = field(default_factory=dict)
    num_nodes: int = 0
    num_edges: int = 0

    # Source metadata
    algorithm: str = ""
    hardware_size: int = 0
    logical_qubits: int = 0
    dag_seed: int = 0
    dag_variant: DagVariant = DagVariant.RAW
    ff_chain_depth: int = 0
    ff_chain_depth_raw: int = 0
    ff_chain_depth_shifted: int | None = None


@dataclass
class CycleRecord:
    cycle: int
    issued: int
    ready_queue_size: int
    waiting_ff_queue_size: int
    in_flight_meas: int
    in_flight_ff: int
    completed_this_cycle: int
    total_done: int


DEFAULT_TAU_PH_US: Final[float] = 1.0


@dataclass
class SimResult:
    dag_label: str
    config: PipelineConfig
    total_nodes: int
    total_cycles: int
    throughput: float
    stall_cycles: int
    stall_rate: float
    utilization: float
    dag_variant: DagVariant
    ff_chain_depth: int
    ff_chain_depth_raw: int
    ff_chain_depth_shifted: int | None
    algorithm: str
    hardware_size: int
    logical_qubits: int
    dag_seed: int
    cycle_records: tuple[CycleRecord, ...] = ()

    @property
    def ilp_profile(self) -> tuple[int, ...]:
        """Ready-queue size at each cycle — proxy for ILP."""
        return tuple(r.ready_queue_size for r in self.cycle_records)
