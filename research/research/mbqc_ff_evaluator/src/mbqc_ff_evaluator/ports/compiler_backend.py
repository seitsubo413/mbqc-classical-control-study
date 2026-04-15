from __future__ import annotations

from typing import Protocol

from mbqc_ff_evaluator.domain.models import ExperimentConfig, OnePercArtifact


class CompilerBackend(Protocol):
    """Port for collecting compiler artifacts."""

    def collect_artifact(self, config: ExperimentConfig) -> OnePercArtifact:
        """Collect an artifact for a single experiment configuration."""
