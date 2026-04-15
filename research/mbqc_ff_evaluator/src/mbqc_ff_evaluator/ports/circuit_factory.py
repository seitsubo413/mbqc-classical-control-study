from __future__ import annotations

from typing import Protocol

from mbqc_ff_evaluator.domain.circuit_models import CircuitProgram
from mbqc_ff_evaluator.domain.models import ExperimentConfig


class CircuitFactory(Protocol):
    """Port for constructing a typed circuit program from an experiment config."""

    def build_program(self, config: ExperimentConfig) -> CircuitProgram:
        """Return a tool-agnostic JCZ program for the requested experiment."""
