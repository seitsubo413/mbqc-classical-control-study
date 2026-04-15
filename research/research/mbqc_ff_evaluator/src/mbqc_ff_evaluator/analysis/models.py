from __future__ import annotations

from dataclasses import dataclass

from mbqc_ff_evaluator.domain.enums import BudgetSelectionMode, ConstraintKind, ReferenceKind


@dataclass(frozen=True)
class MetricsRow:
    algorithm: str
    hardware_size: int
    logical_qubits: int
    seed: int
    status: str
    required_lifetime_layers: float | None
    max_measure_delay_layers: float | None
    ff_chain_depth_raw: float
    ff_chain_depth_shifted: float | None
    depth_reference_kind: ReferenceKind | None
    depth_reference_depth: float | None


@dataclass(frozen=True)
class BudgetRow:
    algorithm: str
    hardware_size: int
    logical_qubits: int
    tau_ph_us: float
    n_seeds: int
    is_coupled: bool
    depth_raw_median: float
    depth_raw_q1: float
    depth_raw_q3: float
    t_ff_cond_ns_median: float
    t_ff_cond_ns_q1: float
    t_ff_cond_ns_q3: float
    depth_shifted_median: float | None
    depth_shifted_q1: float | None
    depth_shifted_q3: float | None
    depth_reference_kind: ReferenceKind | None
    depth_reference_median: float | None
    depth_reference_q1: float | None
    depth_reference_q3: float | None
    t_ff_shifted_ns_median: float | None
    t_ff_shifted_ns_q1: float | None
    t_ff_shifted_ns_q3: float | None
    hold_median: float | None
    meas_median: float | None
    t_hold_ns_median: float | None
    t_hold_ns_q1: float | None
    t_hold_ns_q3: float | None
    t_meas_ns_median: float | None
    t_meas_ns_q1: float | None
    t_meas_ns_q3: float | None
    t_cons_ns_median: float | None
    t_cons_ns_q1: float | None
    t_cons_ns_q3: float | None
    dominant_constraint: ConstraintKind | None


@dataclass(frozen=True)
class BudgetSelection:
    mode: BudgetSelectionMode
    tau_ph_us: float
    hardware_size: int | None = None
    logical_qubits: int | None = None
