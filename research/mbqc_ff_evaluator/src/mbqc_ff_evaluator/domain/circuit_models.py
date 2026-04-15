from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JOperation:
    """OneAdapt JCZ single-qubit operation in quarter-turn units of pi/4."""

    qubit: int
    phase_quarter_turns: float


@dataclass(frozen=True)
class CZOperation:
    """OneAdapt JCZ entangling operation."""

    qubit_a: int
    qubit_b: int


CircuitOperation = JOperation | CZOperation


@dataclass(frozen=True)
class CircuitProgram:
    """Typed, tool-agnostic JCZ program shared across backends."""

    logical_qubits: int
    operations: tuple[CircuitOperation, ...]
