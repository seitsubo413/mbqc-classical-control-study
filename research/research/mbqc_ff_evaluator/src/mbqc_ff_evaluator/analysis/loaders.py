from __future__ import annotations

import csv
from pathlib import Path

from mbqc_ff_evaluator.analysis.models import BudgetRow, MetricsRow
from mbqc_ff_evaluator.domain.enums import ConstraintKind, ReferenceKind


def load_metrics_csv(path: Path) -> list[MetricsRow]:
    rows: list[MetricsRow] = []
    with path.open(encoding="utf-8") as fh:
        for rec in csv.DictReader(fh):
            rows.append(
                MetricsRow(
                    algorithm=rec["algorithm"],
                    hardware_size=int(rec["hardware_size"]),
                    logical_qubits=int(rec["logical_qubits"]),
                    seed=int(rec["seed"]),
                    status=rec["status"],
                    required_lifetime_layers=_opt_float(rec.get("required_lifetime_layers")),
                    max_measure_delay_layers=_opt_float(rec.get("max_measure_delay_layers")),
                    ff_chain_depth_raw=float(rec["ff_chain_depth_raw"]),
                    ff_chain_depth_shifted=_opt_float(rec.get("ff_chain_depth_shifted")),
                    depth_reference_kind=_opt_reference_kind(rec.get("depth_reference_kind")),
                    depth_reference_depth=_opt_float(rec.get("depth_reference_depth")),
                )
            )
    return rows


def load_budgets_csv(path: Path) -> list[BudgetRow]:
    rows: list[BudgetRow] = []
    with path.open(encoding="utf-8") as fh:
        for rec in csv.DictReader(fh):
            rows.append(
                BudgetRow(
                    algorithm=rec["algorithm"],
                    hardware_size=int(rec["hardware_size"]),
                    logical_qubits=int(rec["logical_qubits"]),
                    tau_ph_us=float(rec["tau_ph_us"]),
                    n_seeds=int(rec["n_seeds"]),
                    is_coupled=_parse_bool(rec["is_coupled"]),
                    depth_raw_median=float(rec["depth_raw_median"]),
                    depth_raw_q1=float(rec["depth_raw_q1"]),
                    depth_raw_q3=float(rec["depth_raw_q3"]),
                    t_ff_cond_ns_median=float(rec["t_ff_cond_ns_median"]),
                    t_ff_cond_ns_q1=float(rec["t_ff_cond_ns_q1"]),
                    t_ff_cond_ns_q3=float(rec["t_ff_cond_ns_q3"]),
                    depth_shifted_median=_opt_float(rec.get("depth_shifted_median")),
                    depth_shifted_q1=_opt_float(rec.get("depth_shifted_q1")),
                    depth_shifted_q3=_opt_float(rec.get("depth_shifted_q3")),
                    depth_reference_kind=_opt_reference_kind(rec.get("depth_reference_kind")),
                    depth_reference_median=_opt_float(rec.get("depth_reference_median")),
                    depth_reference_q1=_opt_float(rec.get("depth_reference_q1")),
                    depth_reference_q3=_opt_float(rec.get("depth_reference_q3")),
                    t_ff_shifted_ns_median=_opt_float(rec.get("t_ff_shifted_ns_median")),
                    t_ff_shifted_ns_q1=_opt_float(rec.get("t_ff_shifted_ns_q1")),
                    t_ff_shifted_ns_q3=_opt_float(rec.get("t_ff_shifted_ns_q3")),
                    hold_median=_opt_float(rec.get("hold_median")),
                    meas_median=_opt_float(rec.get("meas_median")),
                    t_hold_ns_median=_opt_float(rec.get("t_hold_ns_median")),
                    t_hold_ns_q1=_opt_float(rec.get("t_hold_ns_q1")),
                    t_hold_ns_q3=_opt_float(rec.get("t_hold_ns_q3")),
                    t_meas_ns_median=_opt_float(rec.get("t_meas_ns_median")),
                    t_meas_ns_q1=_opt_float(rec.get("t_meas_ns_q1")),
                    t_meas_ns_q3=_opt_float(rec.get("t_meas_ns_q3")),
                    t_cons_ns_median=_opt_float(rec.get("t_cons_ns_median")),
                    t_cons_ns_q1=_opt_float(rec.get("t_cons_ns_q1")),
                    t_cons_ns_q3=_opt_float(rec.get("t_cons_ns_q3")),
                    dominant_constraint=_opt_constraint(rec.get("dominant_constraint")),
                )
            )
    return rows


def _opt_float(value: str | None) -> float | None:
    if value is None or value == "" or value == "None":
        return None
    return float(value)


def _parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    raise ValueError(f"cannot parse bool: {value}")


def _opt_constraint(value: str | None) -> ConstraintKind | None:
    if value is None or value == "" or value == "None":
        return None
    return ConstraintKind(value)


def _opt_reference_kind(value: str | None) -> ReferenceKind | None:
    if value is None or value == "" or value == "None":
        return None
    return ReferenceKind(value)
