"""Tests for the cycle-accurate simulator."""
from pathlib import Path

import pytest

from mbqc_pipeline_sim.adapters.artifact_loader import load_dag_from_json
from mbqc_pipeline_sim.core.simulator import MbqcPipelineSimulator
from mbqc_pipeline_sim.domain.enums import DagVariant, ReleaseMode, SchedulingPolicy
from mbqc_pipeline_sim.domain.models import MeasEdge, MeasNode, PipelineConfig, SimDAG


def _run(artifact_path: Path, **kwargs) -> ...:
    dag = load_dag_from_json(artifact_path)
    config = PipelineConfig(**kwargs)
    sim = MbqcPipelineSimulator()
    return sim.run(dag, config)


def _synthetic_dag(nodes: int, edges: list[tuple[int, int]]) -> SimDAG:
    node_items = tuple(MeasNode(node_id=i, phase=None, node_type="M") for i in range(nodes))
    edge_items = tuple(MeasEdge(src=s, dst=d, dependency="x") for s, d in edges)
    indegree = {i: 0 for i in range(nodes)}
    adjacency: dict[int, list[int]] = {i: [] for i in range(nodes)}
    reverse_adj: dict[int, list[int]] = {i: [] for i in range(nodes)}
    for src, dst in edges:
        adjacency[src].append(dst)
        reverse_adj[dst].append(src)
        indegree[dst] += 1

    topo = {i: 0 for i in range(nodes)}
    for src, dst in edges:
        topo[dst] = max(topo[dst], topo[src] + 1)

    remaining = {i: 0 for i in range(nodes)}
    for src, dst in reversed(edges):
        remaining[src] = max(remaining[src], remaining[dst] + 1)

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
        ff_chain_depth_raw=max(topo.values(), default=0),
    )


@pytest.mark.smoke
def test_basic_simulation_qaoa(small_artifact_path: Path) -> None:
    result = _run(small_artifact_path)
    assert result.total_nodes > 0
    assert result.total_cycles >= result.total_nodes
    assert 0.0 < result.throughput <= 1.0
    assert result.stall_rate >= 0.0
    assert len(result.cycle_records) == result.total_cycles


@pytest.mark.smoke
def test_wider_issue_reduces_cycles(small_artifact_path: Path) -> None:
    r1 = _run(small_artifact_path, issue_width=1)
    r4 = _run(small_artifact_path, issue_width=4)
    assert r4.total_cycles <= r1.total_cycles
    assert r4.throughput >= r1.throughput


@pytest.mark.smoke
def test_higher_ff_latency_increases_cycles(qft_artifact_path: Path) -> None:
    r1 = _run(qft_artifact_path, l_ff=1)
    r5 = _run(qft_artifact_path, l_ff=5)
    assert r5.total_cycles >= r1.total_cycles


@pytest.mark.smoke
def test_all_policies_complete(small_artifact_path: Path) -> None:
    for policy in SchedulingPolicy:
        result = _run(small_artifact_path, policy=policy, issue_width=4)
        assert result.total_nodes > 0
        assert result.total_cycles > 0


@pytest.mark.smoke
def test_qft_deeper_chain(qft_artifact_path: Path) -> None:
    result = _run(qft_artifact_path, issue_width=4, l_ff=2)
    assert result.ff_chain_depth_raw > 10
    assert result.stall_rate > 0.0 or result.total_cycles > result.total_nodes


@pytest.mark.smoke
def test_shifted_variant_improves_dynamic_throughput(tmp_path: Path) -> None:
    artifact = {
        "config": {
            "algorithm": "TEST",
            "hardware_size": 1,
            "logical_qubits": 4,
            "seed": 0,
        },
        "ff_nodes": [
            {"node_id": 0, "phase": None, "node_type": "M"},
            {"node_id": 1, "phase": None, "node_type": "M"},
            {"node_id": 2, "phase": None, "node_type": "M"},
            {"node_id": 3, "phase": None, "node_type": "M"},
        ],
        "ff_edges": [
            {"src": 0, "dst": 1, "dependency": "x"},
            {"src": 1, "dst": 2, "dependency": "x"},
            {"src": 2, "dst": 3, "dependency": "x"},
        ],
        "ff_chain_depth_raw": 3,
        "ff_chain_depth_shifted": 1,
        "shifted_dependency_graph": {
            "nodes": [
                {"node_id": 0, "phase": None, "node_type": "M"},
                {"node_id": 1, "phase": None, "node_type": "M"},
                {"node_id": 2, "phase": None, "node_type": "M"},
                {"node_id": 3, "phase": None, "node_type": "M"},
            ],
            "edges": [
                {"src": 0, "dst": 2, "dependency": "x"},
                {"src": 1, "dst": 3, "dependency": "x"},
            ],
            "chain_depth": 1,
        },
    }
    artifact_path = tmp_path / "variant_compare.json"
    artifact_path.write_text(__import__("json").dumps(artifact))

    sim = MbqcPipelineSimulator()
    config = PipelineConfig(
        issue_width=2,
        l_meas=1,
        l_ff=1,
        meas_width=2,
        ff_width=2,
        release_mode=ReleaseMode.NEXT_CYCLE,
    )
    raw_result = sim.run(load_dag_from_json(artifact_path, dag_variant=DagVariant.RAW), config)
    shifted_result = sim.run(load_dag_from_json(artifact_path, dag_variant=DagVariant.SHIFTED), config)

    assert shifted_result.throughput > raw_result.throughput
    assert shifted_result.stall_rate <= raw_result.stall_rate
    assert shifted_result.dag_variant is DagVariant.SHIFTED


@pytest.mark.smoke
def test_next_cycle_release_adds_delay() -> None:
    dag = _synthetic_dag(nodes=2, edges=[(0, 1)])
    sim = MbqcPipelineSimulator()

    same_cycle = sim.run(
        dag,
        PipelineConfig(
            issue_width=1,
            l_meas=1,
            l_ff=1,
            release_mode=ReleaseMode.SAME_CYCLE,
        ),
    )
    next_cycle = sim.run(
        dag,
        PipelineConfig(
            issue_width=1,
            l_meas=1,
            l_ff=1,
            release_mode=ReleaseMode.NEXT_CYCLE,
        ),
    )

    assert next_cycle.total_cycles == same_cycle.total_cycles + 1


@pytest.mark.smoke
def test_ff_width_limits_throughput() -> None:
    dag = _synthetic_dag(nodes=2, edges=[])
    sim = MbqcPipelineSimulator()

    unlimited = sim.run(
        dag,
        PipelineConfig(issue_width=2, l_meas=1, l_ff=2, meas_width=2, ff_width=None),
    )
    ff_bottleneck = sim.run(
        dag,
        PipelineConfig(issue_width=2, l_meas=1, l_ff=2, meas_width=2, ff_width=1),
    )

    assert ff_bottleneck.total_cycles > unlimited.total_cycles


@pytest.mark.smoke
def test_meas_width_limits_throughput() -> None:
    dag = _synthetic_dag(nodes=4, edges=[])
    sim = MbqcPipelineSimulator()

    unlimited = sim.run(
        dag,
        PipelineConfig(issue_width=4, l_meas=1, l_ff=1, meas_width=None, ff_width=None),
    )
    meas_bottleneck = sim.run(
        dag,
        PipelineConfig(issue_width=4, l_meas=1, l_ff=1, meas_width=1, ff_width=None),
    )

    assert meas_bottleneck.total_cycles > unlimited.total_cycles
    assert meas_bottleneck.throughput < unlimited.throughput
