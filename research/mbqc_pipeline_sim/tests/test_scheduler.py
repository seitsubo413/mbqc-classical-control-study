"""Tests for scheduling policies."""
from collections import deque
from pathlib import Path

import pytest

from mbqc_pipeline_sim.adapters.artifact_loader import load_dag_from_json
from mbqc_pipeline_sim.core.scheduler import (
    ASAPScheduler,
    GreedyCriticalScheduler,
    LayerScheduler,
    RandomScheduler,
    RefinedRegimeSwitchScheduler,
    RefinedStallAwareShiftedScheduler,
    RegimeSwitchScheduler,
    SchedulerContext,
    ShiftedCriticalScheduler,
    StallAwareShiftedScheduler,
)
from mbqc_pipeline_sim.domain.enums import SchedulingPolicy
from mbqc_pipeline_sim.domain.models import MeasEdge, MeasNode, PipelineConfig, SimDAG


def _synthetic_dag(nodes: int, edges: list[tuple[int, int]]) -> SimDAG:
    node_items = tuple(MeasNode(node_id=i, phase=None, node_type="M") for i in range(nodes))
    edge_items = tuple(MeasEdge(src=s, dst=d, dependency="x") for s, d in edges)
    adjacency: dict[int, list[int]] = {i: [] for i in range(nodes)}
    reverse_adj: dict[int, list[int]] = {i: [] for i in range(nodes)}
    indegree = {i: 0 for i in range(nodes)}
    outdegree = {i: 0 for i in range(nodes)}

    for src, dst in edges:
        adjacency[src].append(dst)
        reverse_adj[dst].append(src)
        indegree[dst] += 1
        outdegree[src] += 1

    topo = {i: 0 for i in range(nodes)}
    queue: deque[int] = deque(i for i, d in indegree.items() if d == 0)
    pending = dict(indegree)
    while queue:
        node = queue.popleft()
        for succ in adjacency[node]:
            topo[succ] = max(topo[succ], topo[node] + 1)
            pending[succ] -= 1
            if pending[succ] == 0:
                queue.append(succ)

    remaining = {i: 0 for i in range(nodes)}
    queue = deque(i for i, d in outdegree.items() if d == 0)
    pending_out = dict(outdegree)
    while queue:
        node = queue.popleft()
        for pred in reverse_adj[node]:
            remaining[pred] = max(remaining[pred], remaining[node] + 1)
            pending_out[pred] -= 1
            if pending_out[pred] == 0:
                queue.append(pred)

    return SimDAG(
        nodes=node_items,
        edges=edge_items,
        adjacency=adjacency,
        reverse_adj=reverse_adj,
        indegree=indegree,
        topo_level=topo,
        remaining_depth=remaining,
        num_nodes=nodes,
        num_edges=len(edges),
        algorithm="TEST",
        hardware_size=1,
        logical_qubits=nodes,
        dag_seed=0,
        ff_chain_depth=max(topo.values(), default=0),
        ff_chain_depth_raw=max(topo.values(), default=0),
    )


# ── smoke tests (artifact-based) ─────────────────────────────────────────────

@pytest.mark.smoke
def test_asap_returns_limited_nodes(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sched = ASAPScheduler(dag, PipelineConfig())

    sources = [nid for nid, d in dag.indegree.items() if d == 0]
    selected = sched.select(sources, limit=2)
    assert len(selected) <= 2
    assert all(s in sources for s in selected)


@pytest.mark.smoke
def test_layer_only_issues_same_level(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sched = LayerScheduler(dag, PipelineConfig())

    sources = [nid for nid, d in dag.indegree.items() if d == 0]
    selected = sched.select(sources, limit=100)
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

    selected = sched.select(sources, limit=1)
    assert dag.remaining_depth[selected[0]] >= dag.remaining_depth[sources[-1]]


@pytest.mark.smoke
def test_random_is_deterministic_with_seed(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sources = [nid for nid, d in dag.indegree.items() if d == 0]

    s1 = RandomScheduler(dag, PipelineConfig(), seed=42)
    s2 = RandomScheduler(dag, PipelineConfig(), seed=42)
    assert s1.select(sources, 5) == s2.select(sources, 5)


# ── unit tests (synthetic DAG) ────────────────────────────────────────────────

def test_shifted_critical_prefers_deeper_then_earlier_levels() -> None:
    dag = _synthetic_dag(nodes=5, edges=[(0, 3), (3, 4), (1, 4)])
    sched = ShiftedCriticalScheduler(dag, PipelineConfig())

    selected = sched.select([0, 1, 2], limit=2)

    assert selected == [0, 1]


def test_stall_aware_shifted_prefers_ready_nodes_that_unlock_successors() -> None:
    dag = _synthetic_dag(nodes=5, edges=[(0, 3), (1, 4), (2, 4)])
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=4,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED,
    )
    sched = StallAwareShiftedScheduler(dag, config)

    selected = sched.select(
        [0, 1, 2],
        limit=1,
        context=SchedulerContext(remaining_indegree=dict(dag.indegree)),
    )

    assert selected == [0]


def test_stall_aware_shifted_falls_back_when_ff_is_not_bottleneck() -> None:
    dag = _synthetic_dag(nodes=5, edges=[(0, 3), (3, 4), (1, 4)])
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=8,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED,
    )
    sched = StallAwareShiftedScheduler(dag, config)

    selected = sched.select(
        [0, 1, 2],
        limit=2,
        context=SchedulerContext(remaining_indegree=dict(dag.indegree)),
    )

    assert selected == [0, 1]


def test_refined_stall_aware_throttles_limit_under_high_pressure() -> None:
    dag = _synthetic_dag(nodes=5, edges=[(0, 3), (1, 4), (2, 4)])
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=2,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED,
    )
    sched = RefinedStallAwareShiftedScheduler(dag, config)

    # High pressure: ff_waiting_count and meas_in_flight are at or above ff_width
    ctx = SchedulerContext(
        remaining_indegree=dict(dag.indegree),
        ff_waiting_count=2,
        meas_in_flight_count=2,
        ff_in_flight_count=2,
    )
    selected = sched.select([0, 1, 2], limit=8, context=ctx)
    assert len(selected) <= config.ff_width


def test_refined_stall_aware_no_throttle_under_low_pressure() -> None:
    dag = _synthetic_dag(nodes=5, edges=[(0, 3), (1, 4), (2, 4)])
    config = PipelineConfig(
        issue_width=8,
        meas_width=8,
        ff_width=2,
        policy=SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED,
    )
    sched = RefinedStallAwareShiftedScheduler(dag, config)

    # Low pressure: no waiting nodes
    ctx = SchedulerContext(remaining_indegree=dict(dag.indegree))
    selected = sched.select([0, 1, 2], limit=3, context=ctx)
    assert len(selected) == 3


def test_regime_switch_uses_asap_when_fully_provisioned() -> None:
    dag = _synthetic_dag(nodes=5, edges=[(0, 3), (3, 4), (1, 4)])
    config = PipelineConfig(issue_width=4, meas_width=8, ff_width=8)
    sched = RegimeSwitchScheduler(dag, config)

    ctx = SchedulerContext(remaining_indegree=dict(dag.indegree), ff_waiting_count=0)
    selected = sched.select([0, 1, 2], limit=3, context=ctx)
    # ASAP: sort by topo_level then node_id
    assert selected == [0, 1, 2]


def test_regime_switch_uses_stall_aware_under_ff_backpressure() -> None:
    dag = _synthetic_dag(nodes=5, edges=[(0, 3), (1, 4), (2, 4)])
    config = PipelineConfig(issue_width=8, meas_width=8, ff_width=2)
    sched = RegimeSwitchScheduler(dag, config)

    ctx = SchedulerContext(
        remaining_indegree=dict(dag.indegree),
        ff_waiting_count=3,  # backpressure active
    )
    selected = sched.select([0, 1, 2], limit=1, context=ctx)
    # StallAware with FF bottleneck: prefers node 0 (unlocks node 3 alone)
    assert selected == [0]


def test_refined_regime_switch_uses_asap_at_low_pressure() -> None:
    dag = _synthetic_dag(nodes=5, edges=[(0, 3), (3, 4), (1, 4)])
    config = PipelineConfig(issue_width=4, meas_width=8, ff_width=8)
    sched = RefinedRegimeSwitchScheduler(dag, config)

    ctx = SchedulerContext(remaining_indegree=dict(dag.indegree))
    selected = sched.select([0, 1, 2], limit=3, context=ctx)
    assert selected == [0, 1, 2]
