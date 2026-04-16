from __future__ import annotations

from dataclasses import dataclass

from mbqc_pipeline_sim.domain.enums import SchedulerRegime
from mbqc_pipeline_sim.domain.models import PipelineConfig, SimDAG


@dataclass(frozen=True)
class ReadyNodeView:
    node_id: int
    topo_level: int
    remaining_depth: int
    successor_count: int
    unlock_count: int


@dataclass(frozen=True)
class SchedulerContext:
    dag: SimDAG
    config: PipelineConfig
    cycle: int
    issue_limit: int
    ready_nodes: tuple[ReadyNodeView, ...]
    waiting_ff_count: int
    in_flight_meas_count: int
    in_flight_ff_count: int
    meas_slots_available: int | None
    ff_slots_available: int | None


@dataclass(frozen=True)
class SchedulerSignals:
    ff_pressure_score: float
    ff_backpressure_active: bool
    is_ff_bottleneck: bool
    is_fully_provisioned: bool
    recommended_regime: SchedulerRegime


@dataclass(frozen=True)
class SchedulerDecision:
    selected_node_ids: tuple[int, ...]
    rationale: str | None = None
