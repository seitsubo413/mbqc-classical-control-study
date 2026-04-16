from __future__ import annotations

import json
from pathlib import Path

from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus, DependencyKind, ReferenceKind
from mbqc_ff_evaluator.domain.models import (
    DependencyGraphSnapshot,
    DepthReference,
    ExperimentConfig,
    FFEdge,
    FFNode,
    OnePercArtifact,
)


def test_json_repository_roundtrip(tmp_path: Path) -> None:
    repository = JsonArtifactRepository(tmp_path)
    artifact = OnePercArtifact(
        config=ExperimentConfig(
            algorithm=Algorithm.QAOA,
            hardware_size=4,
            logical_qubits=16,
            seed=3,
            refresh=True,
            refresh_bound=20,
        ),
        status=ArtifactStatus.TIMEOUT_GUARD,
        layer_index=float("inf"),
        required_lifetime_layers=None,
        max_measure_delay_layers=9,
        dgraph_num_nodes=3,
        dgraph_num_edges=2,
        ff_nodes=(FFNode(node_id=1, phase=0.5, node_type="Aux"),),
        ff_edges=(FFEdge(src=1, dst=2, dependency=DependencyKind.Z),),
        ff_chain_depth_raw=2,
        ff_chain_depth_shifted=1,
        depth_reference=DepthReference(kind=ReferenceKind.EXACT_GRAPH, depth=1),
        elapsed_sec=0.25,
        shifted_dependency_graph=DependencyGraphSnapshot(
            nodes=(
                FFNode(node_id=1, phase=0.5, node_type="Aux"),
                FFNode(node_id=2, phase=None, node_type="M"),
            ),
            edges=(),
            chain_depth=1,
        ),
        shifted_unavailable_reason=None,
    )

    repository.save_artifact(artifact)
    loaded = repository.load_artifacts()

    assert loaded == (artifact,)


def test_json_repository_loads_legacy_payload_without_shifted_reason(tmp_path: Path) -> None:
    payload = {
        "config": {
            "algorithm": "QAOA",
            "hardware_size": 4,
            "logical_qubits": 16,
            "seed": 3,
            "refresh": True,
            "refresh_bound": 20,
        },
        "status": "success",
        "layer_index": 10.0,
        "required_lifetime_layers": None,
        "max_measure_delay_layers": 9,
        "dgraph_num_nodes": 3,
        "dgraph_num_edges": 2,
        "ff_nodes": [{"node_id": 1, "phase": 0.5, "node_type": "Aux"}],
        "ff_edges": [{"src": 1, "dst": 2, "dependency": "z"}],
        "ff_chain_depth_raw": 2,
        "ff_chain_depth_shifted": None,
        "depth_reference": None,
        "elapsed_sec": 0.25,
        "shifted_dependency_graph": None,
    }
    path = tmp_path / "QAOA_H4_Q16_seed3.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    repository = JsonArtifactRepository(tmp_path)
    loaded = repository.load_artifacts()

    assert len(loaded) == 1
    assert loaded[0].shifted_unavailable_reason is None
