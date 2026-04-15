"""Tests for scheduling policies."""
from pathlib import Path

import pytest

from mbqc_pipeline_sim.adapters.artifact_loader import load_dag_from_json
from mbqc_pipeline_sim.core.scheduler import (
    ASAPScheduler,
    GreedyCriticalScheduler,
    LayerScheduler,
    RandomScheduler,
)


@pytest.mark.smoke
def test_asap_returns_limited_nodes(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sched = ASAPScheduler(dag)

    sources = [nid for nid, d in dag.indegree.items() if d == 0]
    selected = sched.select(sources, limit=2)
    assert len(selected) <= 2
    assert all(s in sources for s in selected)


@pytest.mark.smoke
def test_layer_only_issues_same_level(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sched = LayerScheduler(dag)

    sources = [nid for nid, d in dag.indegree.items() if d == 0]
    selected = sched.select(sources, limit=100)
    levels = {dag.topo_level[n] for n in selected}
    assert len(levels) == 1


@pytest.mark.smoke
def test_greedy_critical_prefers_deeper(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)
    sched = GreedyCriticalScheduler(dag)

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

    s1 = RandomScheduler(dag, seed=42)
    s2 = RandomScheduler(dag, seed=42)
    assert s1.select(sources, 5) == s2.select(sources, 5)
