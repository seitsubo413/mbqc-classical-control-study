from __future__ import annotations

from pathlib import Path
from typing import Sequence

from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus, DependencyKind, ReferenceKind
from mbqc_ff_evaluator.domain.models import (
    ArtifactRecord,
    DepthReference,
    ExperimentConfig,
    FFEdge,
    FFNode,
    OnePercArtifact,
)
from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService


class FakeCompilerBackend:
    def collect_artifact(self, config: ExperimentConfig) -> OnePercArtifact:
        return OnePercArtifact(
            config=config,
            status=ArtifactStatus.SUCCESS,
            layer_index=1.0,
            required_lifetime_layers=2,
            max_measure_delay_layers=3,
            dgraph_num_nodes=2,
            dgraph_num_edges=1,
            ff_nodes=(FFNode(node_id=1, phase=None, node_type="Aux"),),
            ff_edges=(FFEdge(src=1, dst=2, dependency=DependencyKind.X),),
            ff_chain_depth_raw=1,
            ff_chain_depth_shifted=1,
            depth_reference=None,
            elapsed_sec=0.1,
        )


class FakeDepthReferenceBackend:
    def compute_reference(self, config: ExperimentConfig) -> DepthReference:
        _ = config
        return DepthReference(kind=ReferenceKind.INDEPENDENT_COMPILER, depth=4)


class FakeRepository:
    def __init__(self) -> None:
        self.saved: OnePercArtifact | None = None

    def save_artifact(self, artifact: OnePercArtifact) -> ArtifactRecord:
        self.saved = artifact
        return ArtifactRecord(artifact_path=Path("artifact.json"), artifact=artifact)

    def load_artifacts(self) -> Sequence[OnePercArtifact]:
        raise NotImplementedError


def test_artifact_collection_enriches_reference() -> None:
    config = ExperimentConfig(
        algorithm=Algorithm.QAOA,
        hardware_size=4,
        logical_qubits=16,
        seed=0,
        refresh=True,
        refresh_bound=20,
    )
    repository = FakeRepository()
    service = ArtifactCollectionService(
        compiler_backend=FakeCompilerBackend(),
        repository=repository,
        depth_reference_backend=FakeDepthReferenceBackend(),
    )

    artifact = service.collect_in_memory(config)
    assert artifact.depth_reference is not None
    assert artifact.depth_reference.depth == 4
