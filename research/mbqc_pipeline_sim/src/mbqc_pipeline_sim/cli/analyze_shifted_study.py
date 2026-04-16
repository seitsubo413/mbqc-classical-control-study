"""CLI: derive numeric summaries for the shifted-DAG study."""
from __future__ import annotations

import argparse
from pathlib import Path

from mbqc_pipeline_sim.analysis.shifted_study import (
    build_shifted_study_outputs,
    read_sweep_observations,
    write_shifted_study_outputs,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Derive numeric summaries from a shifted-DAG sweep")
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
    outputs = build_shifted_study_outputs(observations)
    write_shifted_study_outputs(outputs, args.output_dir)
    print(f"Analysis outputs saved to {args.output_dir}")


if __name__ == "__main__":
    main()
