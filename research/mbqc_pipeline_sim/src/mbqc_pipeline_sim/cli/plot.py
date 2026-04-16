"""CLI: Generate all figures from sweep results."""
from __future__ import annotations

import argparse
from pathlib import Path

from mbqc_pipeline_sim.visualization.plots import plot_all


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate pipeline-sim figures")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "results" / "summary" / "sweep.csv",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "results" / "figures",
    )
    parser.add_argument(
        "--conservative-input",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "results"
        / "summary"
        / "sweep_conservative_common.csv",
    )
    parser.add_argument(
        "--conservative-meas-input",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "results"
        / "summary"
        / "sweep_conservative_meas_common.csv",
    )
    parser.add_argument(
        "--comparison-input",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "results"
        / "summary"
        / "shifted_comparison.csv",
    )
    args = parser.parse_args(argv)

    plot_all(
        args.input,
        args.outdir,
        conservative_csv=args.conservative_input,
        conservative_meas_csv=args.conservative_meas_input,
        comparison_csv=args.comparison_input,
    )
    print(f"Figures saved to {args.outdir}")


if __name__ == "__main__":
    main()
