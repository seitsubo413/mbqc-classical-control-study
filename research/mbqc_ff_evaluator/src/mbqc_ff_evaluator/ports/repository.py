from __future__ import annotations

from typing import Protocol, Sequence

from mbqc_ff_evaluator.domain.models import ArtifactRecord, OnePercArtifact


class ArtifactRepository(Protocol):
    """Port for persisting experiment artifacts."""

    def save_artifact(self, artifact: OnePercArtifact) -> ArtifactRecord:
        """Persist a single artifact and return its location."""

    def load_artifacts(self) -> Sequence[OnePercArtifact]:
        """Load every persisted artifact."""
