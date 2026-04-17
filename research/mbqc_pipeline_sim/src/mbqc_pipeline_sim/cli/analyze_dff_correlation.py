"""CLI: D_ff vs policy effectiveness correlation analysis (Option 3)."""
from __future__ import annotations

import argparse
from pathlib import Path

from mbqc_pipeline_sim.analysis.shifted_study import (
    build_dff_correlation_bins,
    build_dff_policy_cases,
    read_sweep_observations,
    write_dff_correlation_outputs,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Analyse correlation between D_ff magnitude and policy advantage over ASAP"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "results" / "summary" / "sweep.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "results" / "summary" / "analysis",
    )
    args = parser.parse_args(argv)

    observations = read_sweep_observations(args.input)
    cases = build_dff_policy_cases(observations)
    bins = build_dff_correlation_bins(cases)
    write_dff_correlation_outputs(cases, bins, args.output_dir)
    print(f"D_ff correlation outputs saved to {args.output_dir}")
    print(f"  dff_policy_cases.csv : {len(cases)} rows")
    print(f"  dff_correlation_bins.csv : {len(bins)} rows")


if __name__ == "__main__":
    main()
