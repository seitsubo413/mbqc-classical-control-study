from __future__ import annotations

from typing import Protocol

from mbqc_ff_evaluator.domain.models import DepthReference, ExperimentConfig


class DepthReferenceBackend(Protocol):
    """Port for obtaining a reference depth from another toolchain."""

    def compute_reference(self, config: ExperimentConfig) -> DepthReference | None:
        """Return a depth reference for the given config."""
