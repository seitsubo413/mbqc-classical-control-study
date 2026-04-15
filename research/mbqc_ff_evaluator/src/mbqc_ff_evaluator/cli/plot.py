from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from mbqc_ff_evaluator.analysis.loaders import load_budgets_csv, load_metrics_csv
from mbqc_ff_evaluator.analysis.models import BudgetSelection
from mbqc_ff_evaluator.domain.enums import BudgetSelectionMode
from mbqc_ff_evaluator.visualization.plots import (
    plot_appendix_conservative,
    plot_figure1_divergence,
    plot_figure2_main_budget,
    plot_figure3_triplet_budgets,
    plot_figure4_shifted_budget,
    plot_figure5_lifetime_sensitivity,
    plot_figure6_reference_depth,
    plot_figure7_hardware_width_effect,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate publication figures from summary CSVs")
    parser.add_argument(
        "--summary-dir",
        type=Path,
        default=None,
        help="Directory containing metrics.csv and budgets.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write figures",
    )
    parser.add_argument(
        "--tau-ph-us",
        type=float,
        default=1.0,
        help="Photon lifetime used for budget figures (default: 1.0)",
    )
    parser.add_argument(
        "--sensitivity-algorithm",
        type=str,
        default=None,
        help="Algorithm to use for Figure 3 sensitivity (default: all)",
    )
    parser.add_argument(
        "--selection-mode",
        type=str,
        default=BudgetSelectionMode.COUPLED_ONLY.value,
        choices=[mode.value for mode in BudgetSelectionMode],
        help="Subset of configurations to visualize",
    )
    parser.add_argument(
        "--hardware-size",
        type=int,
        default=None,
        help="Required when selection-mode=fixed_h",
    )
    parser.add_argument(
        "--logical-qubits",
        type=int,
        default=None,
        help="Required when selection-mode=fixed_q",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        choices=["png", "pdf", "svg"],
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parents[3]
    summary_dir = args.summary_dir or base / "results" / "summary"
    output_dir = args.output_dir or base / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    selection = BudgetSelection(
        mode=BudgetSelectionMode(args.selection_mode),
        tau_ph_us=args.tau_ph_us,
        hardware_size=args.hardware_size,
        logical_qubits=args.logical_qubits,
    )

    ext = args.format
    metrics_path = summary_dir / "metrics.csv"
    budgets_path = summary_dir / "budgets.csv"

    generated: list[Path] = []

    if metrics_path.exists():
        metrics = load_metrics_csv(metrics_path)
        p = plot_figure1_divergence(metrics, output_dir / f"fig1_divergence.{ext}")
        generated.append(p)
        print(f"Figure 1: {p}")
    else:
        print(f"Skipping Figure 1: {metrics_path} not found")

    if budgets_path.exists():
        budgets = load_budgets_csv(budgets_path)

        p = plot_figure2_main_budget(
            budgets,
            output_dir / f"fig2_budget.{ext}",
            selection,
        )
        generated.append(p)
        print(f"Figure 2: {p}")

        p = plot_figure3_triplet_budgets(
            budgets,
            output_dir / f"fig3_bottlenecks.{ext}",
            selection,
        )
        generated.append(p)
        print(f"Figure 3: {p}")

        p = plot_figure4_shifted_budget(
            budgets,
            output_dir / f"fig4_shifted_budget.{ext}",
            selection,
        )
        generated.append(p)
        print(f"Figure 4: {p}")

        p = plot_figure5_lifetime_sensitivity(
            budgets,
            output_dir / f"fig5_sensitivity.{ext}",
            selection,
            algorithm=args.sensitivity_algorithm,
        )
        generated.append(p)
        print(f"Figure 5: {p}")

        p = plot_figure6_reference_depth(
            budgets,
            output_dir / f"fig6_reference_depth.{ext}",
            selection,
        )
        generated.append(p)
        print(f"Figure 6: {p}")

        p = plot_figure7_hardware_width_effect(
            budgets,
            output_dir / f"fig7_hardware_width.{ext}",
        )
        generated.append(p)
        print(f"Figure 7: {p}")

        p = plot_appendix_conservative(
            budgets,
            output_dir / f"appendix_conservative.{ext}",
            selection,
        )
        generated.append(p)
        print(f"Appendix: {p}")
    else:
        print(f"Skipping Figures 2-5: {budgets_path} not found")

    print(f"\nGenerated {len(generated)} figures in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
