from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

from mbqc_ff_evaluator.analysis.bottlenecks import dominant_constraint
from mbqc_ff_evaluator.analysis.selection import is_coupled_configuration
from mbqc_ff_evaluator.adapters.csv_repository import BudgetSummaryRow, CsvSummaryRepository
from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.domain.enums import ArtifactStatus
from mbqc_ff_evaluator.domain.models import OnePercArtifact, build_numeric_summary
from mbqc_ff_evaluator.services.compute_budgets import (
    compute_dependency_budget,
    compute_layer_budget,
)

DEFAULT_TAU_PH_US = (0.5, 1.0, 5.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aggregate raw JSON artifacts into CSV summaries")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=None,
        help="Directory containing raw JSON artifacts",
    )
    parser.add_argument(
        "--summary-dir",
        type=Path,
        default=None,
        help="Directory to write summary CSVs",
    )
    parser.add_argument(
        "--tau-ph-us",
        nargs="+",
        type=float,
        default=list(DEFAULT_TAU_PH_US),
        help="Photon lifetime values (μs) for budget computation",
    )
    parser.add_argument(
        "--success-only",
        action="store_true",
        help="Only include successful artifacts in budget aggregation",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parents[3]
    raw_dir = args.raw_dir or base / "results" / "raw"
    summary_dir = args.summary_dir or base / "results" / "summary"

    json_repo = JsonArtifactRepository(raw_dir)
    csv_repo = CsvSummaryRepository(summary_dir)

    artifacts = list(json_repo.load_artifacts())
    if not artifacts:
        print("No artifacts found. Run sweep first.")
        return 1

    metrics_path = csv_repo.write_metrics(artifacts)
    print(f"metrics.csv: {metrics_path}  ({len(artifacts)} rows)")

    budget_rows = _build_budget_rows(
        artifacts,
        tau_ph_us_list=args.tau_ph_us,
        success_only=args.success_only,
    )
    budgets_path = csv_repo.write_budgets(budget_rows)
    print(f"budgets.csv: {budgets_path}  ({len(budget_rows)} rows)")

    summary: dict[str, Any] = {
        "total_artifacts": len(artifacts),
        "budget_rows": len(budget_rows),
        "metrics_path": str(metrics_path),
        "budgets_path": str(budgets_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


GroupKey = tuple[str, int, int]


def _build_budget_rows(
    artifacts: list[OnePercArtifact],
    tau_ph_us_list: list[float],
    success_only: bool,
) -> list[BudgetSummaryRow]:
    groups: dict[GroupKey, list[OnePercArtifact]] = defaultdict(list)
    for art in artifacts:
        if success_only and art.status != ArtifactStatus.SUCCESS:
            continue
        key: GroupKey = (
            art.config.algorithm.value,
            art.config.hardware_size,
            art.config.logical_qubits,
        )
        groups[key].append(art)

    rows: list[BudgetSummaryRow] = []
    for (algo, h, q), group in sorted(groups.items()):
        for tau_ph_us in tau_ph_us_list:
            row = _aggregate_group(algo, h, q, group, tau_ph_us)
            rows.append(row)
    return rows


def _aggregate_group(
    algo: str,
    h: int,
    q: int,
    group: list[OnePercArtifact],
    tau_ph_us: float,
) -> BudgetSummaryRow:
    raw_depths = tuple(float(a.ff_chain_depth_raw) for a in group)
    raw_summary = build_numeric_summary(raw_depths)

    shifted_values = tuple(
        float(a.ff_chain_depth_shifted)
        for a in group
        if a.ff_chain_depth_shifted is not None
    )
    shifted_summary = build_numeric_summary(shifted_values) if shifted_values else None
    reference_values = tuple(
        float(a.depth_reference.depth)
        for a in group
        if a.depth_reference is not None
    )
    reference_summary = build_numeric_summary(reference_values) if reference_values else None
    reference_kind = (
        None
        if not any(a.depth_reference is not None for a in group)
        else next(
            a.depth_reference.kind.value
            for a in group
            if a.depth_reference is not None
        )
    )

    hold_values = tuple(
        float(a.required_lifetime_layers)
        for a in group
        if a.required_lifetime_layers is not None
    )
    hold_summary = build_numeric_summary(hold_values) if hold_values else None

    meas_values = tuple(
        float(a.max_measure_delay_layers)
        for a in group
        if a.max_measure_delay_layers is not None
    )
    meas_summary = build_numeric_summary(meas_values) if meas_values else None

    dep_summary = build_numeric_summary(
        tuple(
            compute_dependency_budget(a.ff_chain_depth_raw, tau_ph_us).t_ff_cond_ns
            for a in group
        )
    )
    shifted_budget_values = tuple(
        compute_dependency_budget(a.ff_chain_depth_shifted, tau_ph_us).t_ff_cond_ns
        for a in group
        if a.ff_chain_depth_shifted is not None
    )
    shifted_budget_summary = (
        build_numeric_summary(shifted_budget_values) if shifted_budget_values else None
    )
    hold_budget_values = tuple(
        compute_layer_budget(a.required_lifetime_layers, tau_ph_us).per_layer_budget_ns
        for a in group
        if a.required_lifetime_layers is not None
    )
    hold_budget_summary = (
        build_numeric_summary(hold_budget_values) if hold_budget_values else None
    )
    meas_budget_values = tuple(
        compute_layer_budget(a.max_measure_delay_layers, tau_ph_us).per_layer_budget_ns
        for a in group
        if a.max_measure_delay_layers is not None
    )
    meas_budget_summary = (
        build_numeric_summary(meas_budget_values) if meas_budget_values else None
    )
    conservative_values = tuple(
        min(
            compute_dependency_budget(a.ff_chain_depth_raw, tau_ph_us).t_ff_cond_ns,
            compute_layer_budget(a.required_lifetime_layers, tau_ph_us).per_layer_budget_ns,
            compute_layer_budget(a.max_measure_delay_layers, tau_ph_us).per_layer_budget_ns,
        )
        for a in group
        if a.required_lifetime_layers is not None and a.max_measure_delay_layers is not None
    )
    conservative_summary = (
        build_numeric_summary(conservative_values) if conservative_values else None
    )
    dominant = dominant_constraint(
        dependency_ns=dep_summary.median,
        hold_ns=hold_budget_summary.median if hold_budget_summary is not None else None,
        measurement_ns=meas_budget_summary.median if meas_budget_summary is not None else None,
    )

    return BudgetSummaryRow(
        algorithm=algo,
        hardware_size=h,
        logical_qubits=q,
        tau_ph_us=tau_ph_us,
        n_seeds=len(group),
        is_coupled=is_coupled_configuration(h, q),
        depth_raw_median=raw_summary.median,
        depth_raw_q1=raw_summary.q1,
        depth_raw_q3=raw_summary.q3,
        depth_raw_mean=raw_summary.mean,
        depth_shifted_median=shifted_summary.median if shifted_summary else None,
        depth_shifted_q1=shifted_summary.q1 if shifted_summary else None,
        depth_shifted_q3=shifted_summary.q3 if shifted_summary else None,
        depth_reference_kind=reference_kind,
        depth_reference_median=reference_summary.median if reference_summary else None,
        depth_reference_q1=reference_summary.q1 if reference_summary else None,
        depth_reference_q3=reference_summary.q3 if reference_summary else None,
        t_ff_shifted_ns_median=shifted_budget_summary.median if shifted_budget_summary else None,
        t_ff_shifted_ns_q1=shifted_budget_summary.q1 if shifted_budget_summary else None,
        t_ff_shifted_ns_q3=shifted_budget_summary.q3 if shifted_budget_summary else None,
        hold_median=hold_summary.median if hold_summary else None,
        hold_q1=hold_summary.q1 if hold_summary else None,
        hold_q3=hold_summary.q3 if hold_summary else None,
        meas_median=meas_summary.median if meas_summary else None,
        meas_q1=meas_summary.q1 if meas_summary else None,
        meas_q3=meas_summary.q3 if meas_summary else None,
        t_ff_cond_ns_median=dep_summary.median,
        t_ff_cond_ns_q1=dep_summary.q1,
        t_ff_cond_ns_q3=dep_summary.q3,
        t_hold_ns_median=hold_budget_summary.median if hold_budget_summary else None,
        t_hold_ns_q1=hold_budget_summary.q1 if hold_budget_summary else None,
        t_hold_ns_q3=hold_budget_summary.q3 if hold_budget_summary else None,
        t_meas_ns_median=meas_budget_summary.median if meas_budget_summary else None,
        t_meas_ns_q1=meas_budget_summary.q1 if meas_budget_summary else None,
        t_meas_ns_q3=meas_budget_summary.q3 if meas_budget_summary else None,
        t_cons_ns_median=conservative_summary.median if conservative_summary else None,
        t_cons_ns_q1=conservative_summary.q1 if conservative_summary else None,
        t_cons_ns_q3=conservative_summary.q3 if conservative_summary else None,
        dominant_constraint=dominant,
    )


if __name__ == "__main__":
    raise SystemExit(main())
