from __future__ import annotations


class InvalidArtifactError(ValueError):
    """Raised when an FF-evaluator artifact cannot be converted into a valid DAG."""


class SimulationDeadlockError(RuntimeError):
    """Raised when the simulator cannot make progress on a non-empty DAG."""
