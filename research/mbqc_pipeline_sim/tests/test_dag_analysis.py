"""Tests for DAG loading and static analysis."""
import json
from pathlib import Path

import pytest

from mbqc_pipeline_sim.adapters.artifact_loader import load_dag_from_json
from mbqc_pipeline_sim.core.dag_analysis import (
    critical_path_length,
    level_width_histogram,
    max_parallelism,
)
from mbqc_pipeline_sim.domain.enums import DagVariant
from mbqc_pipeline_sim.domain.errors import InvalidArtifactError


@pytest.mark.smoke
def test_load_and_analyse_qaoa(small_artifact_path: Path) -> None:
    dag = load_dag_from_json(small_artifact_path)

    assert dag.num_nodes > 0
    assert dag.num_edges > 0
    assert dag.algorithm == "QAOA"
    assert dag.dag_variant is DagVariant.RAW
    assert len(dag.topo_level) == dag.num_nodes
    assert len(dag.remaining_depth) == dag.num_nodes

    cpl = critical_path_length(dag)
    assert cpl == dag.ff_chain_depth
    assert cpl == dag.ff_chain_depth_raw

    hist = level_width_histogram(dag)
    assert sum(hist.values()) == dag.num_nodes

    mp = max_parallelism(dag)
    assert mp >= 1


@pytest.mark.smoke
def test_load_and_analyse_qft(qft_artifact_path: Path) -> None:
    dag = load_dag_from_json(qft_artifact_path)

    assert dag.algorithm == "QFT"
    cpl = critical_path_length(dag)
    assert cpl == dag.ff_chain_depth
    assert cpl == dag.ff_chain_depth_raw
    assert cpl > 0


@pytest.mark.smoke
def test_load_shifted_variant_uses_shifted_topology(tmp_path: Path) -> None:
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
    path = tmp_path / "shifted.json"
    path.write_text(json.dumps(artifact))

    raw_dag = load_dag_from_json(path, dag_variant=DagVariant.RAW)
    shifted_dag = load_dag_from_json(path, dag_variant=DagVariant.SHIFTED)

    assert raw_dag.num_edges == 3
    assert shifted_dag.num_edges == 2
    assert raw_dag.ff_chain_depth == 3
    assert shifted_dag.ff_chain_depth == 1
    assert shifted_dag.dag_variant is DagVariant.SHIFTED


@pytest.mark.smoke
def test_invalid_edge_endpoint_raises(tmp_path: Path) -> None:
    artifact = {
        "config": {
            "algorithm": "TEST",
            "hardware_size": 1,
            "logical_qubits": 2,
            "seed": 0,
        },
        "ff_nodes": [
            {"node_id": 0, "phase": None, "node_type": "M"},
            {"node_id": 1, "phase": None, "node_type": "M"},
        ],
        "ff_edges": [
            {"src": 0, "dst": 99, "dependency": "x"},
        ],
        "ff_chain_depth_raw": 1,
    }
    path = tmp_path / "invalid_edge.json"
    path.write_text(json.dumps(artifact))

    with pytest.raises(InvalidArtifactError):
        load_dag_from_json(path)


@pytest.mark.smoke
def test_cycle_raises(tmp_path: Path) -> None:
    artifact = {
        "config": {
            "algorithm": "TEST",
            "hardware_size": 1,
            "logical_qubits": 2,
            "seed": 0,
        },
        "ff_nodes": [
            {"node_id": 0, "phase": None, "node_type": "M"},
            {"node_id": 1, "phase": None, "node_type": "M"},
        ],
        "ff_edges": [
            {"src": 0, "dst": 1, "dependency": "x"},
            {"src": 1, "dst": 0, "dependency": "x"},
        ],
        "ff_chain_depth_raw": 2,
    }
    path = tmp_path / "cycle.json"
    path.write_text(json.dumps(artifact))

    with pytest.raises(InvalidArtifactError):
        load_dag_from_json(path)
