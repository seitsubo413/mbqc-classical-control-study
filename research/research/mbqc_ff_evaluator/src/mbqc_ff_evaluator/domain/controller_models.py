from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerModel:
    """Simple clocked classical controller model for FF-stage evaluation."""

    name: str
    clock_mhz: float
    cycles_per_stage: int
    fixed_overhead_ns: float = 0.0
    notes: str = ""


@dataclass(frozen=True)
class ControllerEvaluation:
    algorithm: str
    hardware_size: int
    logical_qubits: int
    tau_ph_us: float
    budget_kind: str
    budget_ns: float
    controller_name: str
    controller_latency_ns: float
    slack_ns: float
    feasible: bool
