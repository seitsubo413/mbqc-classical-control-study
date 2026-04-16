"""Pure helpers for building scheduler-facing runtime features."""
from __future__ import annotations

from mbqc_pipeline_sim.domain.models import PipelineConfig, SimDAG
from mbqc_pipeline_sim.domain.scheduler_models import ReadyNodeView, SchedulerContext


def build_scheduler_context(
    *,
    dag: SimDAG,
    config: PipelineConfig,
    cycle: int,
    ready: tuple[int, ...],
    issue_limit: int,
    remaining_indegree: dict[int, int],
    waiting_ff_count: int,
    in_flight_meas_count: int,
    in_flight_ff_count: int,
    meas_slots_available: int | None,
    ff_slots_available: int | None,
) -> SchedulerContext:
    return SchedulerContext(
        dag=dag,
        config=config,
        cycle=cycle,
        issue_limit=issue_limit,
        ready_nodes=tuple(
            _build_ready_node_view(dag=dag, node_id=node_id, remaining_indegree=remaining_indegree)
            for node_id in ready
        ),
        waiting_ff_count=waiting_ff_count,
        in_flight_meas_count=in_flight_meas_count,
        in_flight_ff_count=in_flight_ff_count,
        meas_slots_available=meas_slots_available,
        ff_slots_available=ff_slots_available,
    )


def _build_ready_node_view(
    *,
    dag: SimDAG,
    node_id: int,
    remaining_indegree: dict[int, int],
) -> ReadyNodeView:
    successors = dag.adjacency.get(node_id, [])
    unlock_count = sum(1 for succ in successors if remaining_indegree.get(succ, 0) == 1)
    return ReadyNodeView(
        node_id=node_id,
        topo_level=dag.topo_level.get(node_id, 0),
        remaining_depth=dag.remaining_depth.get(node_id, 0),
        successor_count=len(successors),
        unlock_count=unlock_count,
    )
