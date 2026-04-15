from __future__ import annotations

from dataclasses import replace

from mbqc_ff_evaluator.domain.models import ArtifactRecord, ExperimentConfig, OnePercArtifact
from mbqc_ff_evaluator.ports.compiler_backend import CompilerBackend
from mbqc_ff_evaluator.ports.depth_reference import DepthReferenceBackend
from mbqc_ff_evaluator.ports.repository import ArtifactRepository


class ArtifactCollectionService:
    """Collect, enrich, and persist a single experiment artifact."""

    def __init__(
        self,
        compiler_backend: CompilerBackend,
        repository: ArtifactRepository,
        depth_reference_backend: DepthReferenceBackend | None = None,
    ) -> None:
        self._compiler_backend = compiler_backend
        self._repository = repository
        self._depth_reference_backend = depth_reference_backend

    def collect(self, config: ExperimentConfig) -> ArtifactRecord:
        artifact = self._compiler_backend.collect_artifact(config)
        if self._depth_reference_backend is not None:
            depth_reference = self._depth_reference_backend.compute_reference(config)
            artifact = replace(artifact, depth_reference=depth_reference)
        return self._repository.save_artifact(artifact)

    def collect_in_memory(self, config: ExperimentConfig) -> OnePercArtifact:
        artifact = self._compiler_backend.collect_artifact(config)
        if self._depth_reference_backend is None:
            return artifact
        depth_reference = self._depth_reference_backend.compute_reference(config)
        return replace(artifact, depth_reference=depth_reference)
