from __future__ import annotations

from pathlib import Path

from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus, DependencyKind, ReferenceKind
from mbqc_ff_evaluator.domain.models import (
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
        ff_chain_depth_shifted=None,
        depth_reference=DepthReference(kind=ReferenceKind.EXACT_GRAPH, depth=1),
        elapsed_sec=0.25,
    )

    repository.save_artifact(artifact)
    loaded = repository.load_artifacts()

    assert loaded == (artifact,)
