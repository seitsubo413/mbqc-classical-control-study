"""Tests for scheduling policies."""
from pathlib import Path

import pytest

from mbqc_pipeline_sim.adapters.artifact_loader import load_dag_from_json
from mbqc_pipeline_sim.core.scheduler import build_scheduler
from mbqc_pipeline_sim.core.scheduler_features import build_scheduler_context
from mbqc_pipeline_sim.core.scheduler_signals import (
    build_scheduler_signals,
    refined_stall_aware_issue_limit,
)
from mbqc_pipeline_sim.core.scheduler import (
    ASAPScheduler,
    GreedyCriticalScheduler,
    LayerScheduler,
    RefinedStallAwareShiftedScheduler,
    RefinedRegimeSwitchScheduler,
    RegimeSwitchScheduler,
    RandomScheduler,
    StallAwareShiftedScheduler,
    ShiftedCriticalScheduler,
)
from mbqc_pipeline_sim.domain.enums import SchedulerRegime, SchedulingPolicy
from mbqc_pipeline_sim.domain.models import PipelineConfig
from mbqc_pipeline_sim.domain.scheduler_models import ReadyNodeView, SchedulerContext
from mbqc_pipeline_sim.domain.models import SimDAG


@pytest.mark.smoke
def test_asap_returns_limited_nodes(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sched = ASAPScheduler(dag, PipelineConfig())

    sources = [nid for nid, d in dag.indegree.items() if d == 0]
    context = _build_context(dag, sources, limit=2)
    selected = sched.select(context).selected_node_ids
    assert len(selected) <= 2
    assert all(s in sources for s in selected)


@pytest.mark.smoke
def test_layer_only_issues_same_level(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sched = LayerScheduler(dag, PipelineConfig())

    sources = [nid for nid, d in dag.indegree.items() if d == 0]
    context = _build_context(dag, sources, limit=100)
    selected = sched.select(context).selected_node_ids
    levels = {dag.topo_level[n] for n in selected}
    assert len(levels) == 1


@pytest.mark.smoke
def test_greedy_critical_prefers_deeper(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sched = GreedyCriticalScheduler(dag, PipelineConfig())

    sources = sorted(
        [nid for nid, d in dag.indegree.items() if d == 0],
        key=lambda n: -dag.remaining_depth.get(n, 0),
    )
    if len(sources) < 2:
        pytest.skip("too few source nodes")

    context = _build_context(dag, sources, limit=1)
    selected = sched.select(context).selected_node_ids
    assert dag.remaining_depth[selected[0]] >= dag.remaining_depth[sources[-1]]


@pytest.mark.smoke
def test_random_is_deterministic_with_seed(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sources = [nid for nid, d in dag.indegree.items() if d == 0]

    config = PipelineConfig(seed=42)
    context = _build_context(dag, sources, limit=5)
    s1 = RandomScheduler(dag, config)
    s2 = RandomScheduler(dag, config)
    assert s1.select(context).selected_node_ids == s2.select(context).selected_node_ids


def test_shifted_critical_breaks_tie_with_unlock_count() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(issue_width=1, policy=SchedulingPolicy.SHIFTED_CRITICAL)
    sched = ShiftedCriticalScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=0,
        issue_limit=1,
        ready_nodes=(
            ReadyNodeView(
                node_id=7,
                topo_level=0,
                remaining_depth=5,
                successor_count=1,
                unlock_count=1,
            ),
            ReadyNodeView(
                node_id=3,
                topo_level=0,
                remaining_depth=5,
                successor_count=2,
                unlock_count=3,
            ),
        ),
        waiting_ff_count=0,
        in_flight_meas_count=0,
        in_flight_ff_count=0,
        meas_slots_available=1,
        ff_slots_available=1,
    )

    selected = sched.select(context).selected_node_ids
    assert selected == (3,)


def test_build_scheduler_supports_shifted_critical() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(policy=SchedulingPolicy.SHIFTED_CRITICAL)
    scheduler = build_scheduler(SchedulingPolicy.SHIFTED_CRITICAL, dag, config=config)
    assert isinstance(scheduler, ShiftedCriticalScheduler)


def test_stall_aware_shifted_caps_issue_under_ff_backpressure() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        ff_width=4,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED,
    )
    sched = StallAwareShiftedScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=3,
        issue_limit=8,
        ready_nodes=tuple(
            ReadyNodeView(
                node_id=node_id,
                topo_level=0,
                remaining_depth=1,
                successor_count=1,
                unlock_count=1,
            )
            for node_id in range(8)
        ),
        waiting_ff_count=2,
        in_flight_meas_count=0,
        in_flight_ff_count=4,
        meas_slots_available=8,
        ff_slots_available=0,
    )

    decision = sched.select(context)
    assert len(decision.selected_node_ids) == 4
    assert decision.rationale == "ff_backpressure"


def test_stall_aware_shifted_prefers_lower_unlock_when_pressured() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        ff_width=4,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED,
    )
    sched = StallAwareShiftedScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=2,
        issue_limit=2,
        ready_nodes=(
            ReadyNodeView(
                node_id=9,
                topo_level=0,
                remaining_depth=5,
                successor_count=3,
                unlock_count=4,
            ),
            ReadyNodeView(
                node_id=4,
                topo_level=0,
                remaining_depth=4,
                successor_count=1,
                unlock_count=1,
            ),
        ),
        waiting_ff_count=1,
        in_flight_meas_count=0,
        in_flight_ff_count=4,
        meas_slots_available=2,
        ff_slots_available=0,
    )

    decision = sched.select(context)
    assert decision.selected_node_ids == (4, 9)


def test_build_scheduler_supports_stall_aware_shifted() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(policy=SchedulingPolicy.STALL_AWARE_SHIFTED)
    scheduler = build_scheduler(SchedulingPolicy.STALL_AWARE_SHIFTED, dag, config=config)
    assert isinstance(scheduler, StallAwareShiftedScheduler)


def test_refined_stall_aware_keeps_full_issue_at_low_pressure() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        ff_width=4,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED,
    )
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=0,
        issue_limit=8,
        ready_nodes=(),
        waiting_ff_count=0,
        in_flight_meas_count=1,
        in_flight_ff_count=1,
        meas_slots_available=8,
        ff_slots_available=4,
    )

    signals = build_scheduler_signals(context)
    assert refined_stall_aware_issue_limit(context, signals) == 8


def test_refined_stall_aware_scales_issue_limit_at_moderate_pressure() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        ff_width=4,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED,
    )
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=2,
        issue_limit=8,
        ready_nodes=tuple(
            ReadyNodeView(
                node_id=node_id,
                topo_level=0,
                remaining_depth=2,
                successor_count=1,
                unlock_count=node_id % 3,
            )
            for node_id in range(8)
        ),
        waiting_ff_count=2,
        in_flight_meas_count=3,
        in_flight_ff_count=2,
        meas_slots_available=8,
        ff_slots_available=2,
    )

    signals = build_scheduler_signals(context)
    assert refined_stall_aware_issue_limit(context, signals) == 5

    sched = RefinedStallAwareShiftedScheduler(dag, config)
    decision = sched.select(context)
    assert len(decision.selected_node_ids) == 5
    assert decision.rationale == "ff_pressure_throttled"


def test_refined_stall_aware_caps_to_ff_width_at_high_pressure() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        ff_width=4,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED,
    )
    sched = RefinedStallAwareShiftedScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=3,
        issue_limit=8,
        ready_nodes=tuple(
            ReadyNodeView(
                node_id=node_id,
                topo_level=0,
                remaining_depth=1,
                successor_count=1,
                unlock_count=1,
            )
            for node_id in range(8)
        ),
        waiting_ff_count=4,
        in_flight_meas_count=4,
        in_flight_ff_count=4,
        meas_slots_available=8,
        ff_slots_available=0,
    )

    decision = sched.select(context)
    assert len(decision.selected_node_ids) == 4
    assert decision.rationale == "ff_pressure_throttled"


def test_build_scheduler_supports_refined_stall_aware_shifted() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(policy=SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED)
    scheduler = build_scheduler(SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED, dag, config=config)
    assert isinstance(scheduler, RefinedStallAwareShiftedScheduler)


def test_regime_switch_uses_asap_in_fully_provisioned_regime() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=8,
        policy=SchedulingPolicy.REGIME_SWITCH,
    )
    sched = RegimeSwitchScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=0,
        issue_limit=1,
        ready_nodes=(
            ReadyNodeView(
                node_id=9,
                topo_level=1,
                remaining_depth=10,
                successor_count=4,
                unlock_count=4,
            ),
            ReadyNodeView(
                node_id=2,
                topo_level=0,
                remaining_depth=1,
                successor_count=1,
                unlock_count=1,
            ),
        ),
        waiting_ff_count=0,
        in_flight_meas_count=0,
        in_flight_ff_count=0,
        meas_slots_available=8,
        ff_slots_available=8,
    )

    decision = sched.select(context)
    assert decision.selected_node_ids == (2,)
    assert decision.rationale == "asap_regime"


def test_regime_switch_uses_shifted_critical_in_mixed_regime() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=6,
        policy=SchedulingPolicy.REGIME_SWITCH,
    )
    sched = RegimeSwitchScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=1,
        issue_limit=1,
        ready_nodes=(
            ReadyNodeView(
                node_id=9,
                topo_level=1,
                remaining_depth=10,
                successor_count=1,
                unlock_count=1,
            ),
            ReadyNodeView(
                node_id=2,
                topo_level=0,
                remaining_depth=2,
                successor_count=4,
                unlock_count=4,
            ),
        ),
        waiting_ff_count=0,
        in_flight_meas_count=0,
        in_flight_ff_count=0,
        meas_slots_available=8,
        ff_slots_available=6,
    )

    decision = sched.select(context)
    assert decision.selected_node_ids == (9,)
    assert decision.rationale == "shifted_critical_regime"


def test_regime_switch_v1_uses_stall_aware_under_moderate_ff_pressure() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=4,
        policy=SchedulingPolicy.REGIME_SWITCH,
    )
    sched = RegimeSwitchScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=2,
        issue_limit=1,
        ready_nodes=(
            ReadyNodeView(
                node_id=9,
                topo_level=0,
                remaining_depth=6,
                successor_count=1,
                unlock_count=4,
            ),
            ReadyNodeView(
                node_id=4,
                topo_level=0,
                remaining_depth=4,
                successor_count=4,
                unlock_count=1,
            ),
        ),
        waiting_ff_count=1,
        in_flight_meas_count=2,
        in_flight_ff_count=3,
        meas_slots_available=6,
        ff_slots_available=2,
    )

    decision = sched.select(context)
    assert decision.selected_node_ids == (4,)
    assert decision.rationale == "stall_aware_regime"


def test_regime_switch_keeps_shifted_critical_under_moderate_ff_pressure() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=4,
        policy=SchedulingPolicy.REGIME_SWITCH_REFINED,
    )
    sched = RefinedRegimeSwitchScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=2,
        issue_limit=1,
        ready_nodes=(
            ReadyNodeView(
                node_id=9,
                topo_level=0,
                remaining_depth=6,
                successor_count=1,
                unlock_count=4,
            ),
            ReadyNodeView(
                node_id=4,
                topo_level=0,
                remaining_depth=4,
                successor_count=4,
                unlock_count=1,
            ),
        ),
        waiting_ff_count=1,
        in_flight_meas_count=2,
        in_flight_ff_count=3,
        meas_slots_available=6,
        ff_slots_available=2,
    )

    decision = sched.select(context)
    assert decision.selected_node_ids == (9,)
    assert decision.rationale == "shifted_critical_regime"


def test_regime_switch_uses_stall_aware_under_ff_backpressure() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=4,
        policy=SchedulingPolicy.REGIME_SWITCH,
    )
    sched = RegimeSwitchScheduler(dag, config)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=2,
        issue_limit=2,
        ready_nodes=(
            ReadyNodeView(
                node_id=9,
                topo_level=0,
                remaining_depth=6,
                successor_count=4,
                unlock_count=4,
            ),
            ReadyNodeView(
                node_id=4,
                topo_level=0,
                remaining_depth=4,
                successor_count=1,
                unlock_count=1,
            ),
        ),
        waiting_ff_count=1,
        in_flight_meas_count=4,
        in_flight_ff_count=4,
        meas_slots_available=2,
        ff_slots_available=0,
    )

    decision = sched.select(context)
    assert decision.selected_node_ids == (4, 9)
    assert decision.rationale == "stall_aware_regime"


def test_build_scheduler_supports_regime_switch() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(policy=SchedulingPolicy.REGIME_SWITCH)
    scheduler = build_scheduler(SchedulingPolicy.REGIME_SWITCH, dag, config=config)
    assert isinstance(scheduler, RegimeSwitchScheduler)


def test_build_scheduler_supports_refined_regime_switch() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(policy=SchedulingPolicy.REGIME_SWITCH_REFINED)
    scheduler = build_scheduler(SchedulingPolicy.REGIME_SWITCH_REFINED, dag, config=config)
    assert isinstance(scheduler, RefinedRegimeSwitchScheduler)


def test_build_scheduler_signals_reports_stall_aware_regime() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(issue_width=8, meas_width=8, ff_width=4)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=3,
        issue_limit=4,
        ready_nodes=(),
        waiting_ff_count=4,
        in_flight_meas_count=4,
        in_flight_ff_count=4,
        meas_slots_available=4,
        ff_slots_available=0,
    )

    signals = build_scheduler_signals(context)
    assert signals.ff_backpressure_active is True
    assert signals.is_ff_bottleneck is True
    assert signals.recommended_regime is SchedulerRegime.STALL_AWARE


def test_build_scheduler_signals_reports_asap_regime() -> None:
    dag = SimDAG(nodes=(), edges=())
    config = PipelineConfig(issue_width=8, meas_width=8, ff_width=8)
    context = SchedulerContext(
        dag=dag,
        config=config,
        cycle=0,
        issue_limit=8,
        ready_nodes=(),
        waiting_ff_count=0,
        in_flight_meas_count=0,
        in_flight_ff_count=0,
        meas_slots_available=8,
        ff_slots_available=8,
    )

    signals = build_scheduler_signals(context)
    assert signals.ff_pressure_score == 0.0
    assert signals.is_fully_provisioned is True
    assert signals.recommended_regime is SchedulerRegime.ASAP


def _build_context(dag, ready: list[int], *, limit: int):
    return build_scheduler_context(
        dag=dag,
        config=PipelineConfig(issue_width=max(limit, 1)),
        cycle=0,
        ready=tuple(ready),
        issue_limit=limit,
        remaining_indegree=dag.indegree,
        waiting_ff_count=0,
        in_flight_meas_count=0,
        in_flight_ff_count=0,
        meas_slots_available=limit,
        ff_slots_available=limit,
    )
