from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from mbqc_ff_evaluator.analysis.loaders import load_budgets_csv
from mbqc_ff_evaluator.analysis.models import BudgetSelection
from mbqc_ff_evaluator.analysis.selection import filter_budget_rows
from mbqc_ff_evaluator.domain.controller_models import ControllerModel
from mbqc_ff_evaluator.domain.enums import BudgetSelectionMode
from mbqc_ff_evaluator.services.controller_budget import evaluate_budget_row


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate simple controller models against budget summaries")
    parser.add_argument("--summary-dir", type=Path, default=None)
    parser.add_argument("--output-path", type=Path, default=None)
    parser.add_argument("--tau-ph-us", type=float, default=1.0)
    parser.add_argument(
        "--selection-mode",
        type=str,
        default=BudgetSelectionMode.COUPLED_ONLY.value,
        choices=[mode.value for mode in BudgetSelectionMode],
    )
    parser.add_argument("--hardware-size", type=int, default=None)
    parser.add_argument("--logical-qubits", type=int, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parents[3]
    summary_dir = args.summary_dir or base / "results" / "summary"
    output_path = args.output_path or summary_dir / "controller_budget_eval.csv"

    budgets = load_budgets_csv(summary_dir / "budgets.csv")
    selection = BudgetSelection(
        mode=BudgetSelectionMode(args.selection_mode),
        tau_ph_us=args.tau_ph_us,
        hardware_size=args.hardware_size,
        logical_qubits=args.logical_qubits,
    )
    selected_rows = filter_budget_rows(budgets, selection)

    models = _default_models()
    evaluations = []
    for row in selected_rows:
        evaluations.extend(evaluate_budget_row(row, models))

    _write_rows(output_path, evaluations)
    print(
        json.dumps(
            {
                "output_path": str(output_path),
                "n_budget_rows": len(selected_rows),
                "n_evaluations": len(evaluations),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _default_models() -> tuple[ControllerModel, ...]:
    return (
        ControllerModel(
            name="opx_like_250ns",
            clock_mhz=1000.0,
            cycles_per_stage=0,
            fixed_overhead_ns=250.0,
            notes="Reference-class feedback latency",
        ),
        ControllerModel(
            name="xcom_like_185ns",
            clock_mhz=1000.0,
            cycles_per_stage=0,
            fixed_overhead_ns=185.0,
            notes="Reference-class fast controller target",
        ),
        ControllerModel(
            name="clocked_1ghz_5cy",
            clock_mhz=1000.0,
            cycles_per_stage=5,
            fixed_overhead_ns=0.0,
            notes="Simple pipelined synchronous controller",
        ),
        ControllerModel(
            name="clocked_2ghz_5cy",
            clock_mhz=2000.0,
            cycles_per_stage=5,
            fixed_overhead_ns=0.0,
            notes="More aggressive synchronous controller",
        ),
        ControllerModel(
            name="cmos_10ns_target",
            clock_mhz=1000.0,
            cycles_per_stage=0,
            fixed_overhead_ns=10.0,
            notes="Aspirational near-term custom controller target",
        ),
    )


def _write_rows(path: Path, rows: Sequence[Any]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    header = list(asdict(rows[0]).keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


if __name__ == "__main__":
    raise SystemExit(main())
