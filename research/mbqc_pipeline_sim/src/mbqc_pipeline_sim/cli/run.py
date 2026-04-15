"""CLI: Run a single simulation on one artifact JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mbqc_pipeline_sim.adapters.artifact_loader import load_dag_from_json
from mbqc_pipeline_sim.core.simulator import MbqcPipelineSimulator
from mbqc_pipeline_sim.domain.enums import ReleaseMode, SchedulingPolicy
from mbqc_pipeline_sim.domain.models import PipelineConfig


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run MBQC pipeline simulation")
    parser.add_argument("artifact", type=Path, help="Path to FF-evaluator JSON artifact")
    parser.add_argument("-W", "--issue-width", type=int, default=1)
    parser.add_argument("--l-meas", type=int, default=1)
    parser.add_argument("--l-ff", type=int, default=1)
    parser.add_argument("--meas-width", type=int, default=None)
    parser.add_argument("--ff-width", type=int, default=None)
    parser.add_argument(
        "--release-mode",
        type=str,
        default=ReleaseMode.SAME_CYCLE.value,
        choices=[m.value for m in ReleaseMode],
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="asap",
        choices=[p.value for p in SchedulingPolicy],
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    dag = load_dag_from_json(args.artifact)
    config = PipelineConfig(
        issue_width=args.issue_width,
        l_meas=args.l_meas,
        l_ff=args.l_ff,
        meas_width=args.meas_width,
        ff_width=args.ff_width,
        release_mode=ReleaseMode(args.release_mode),
        policy=SchedulingPolicy(args.policy),
        seed=args.seed,
    )

    sim = MbqcPipelineSimulator()
    result = sim.run(dag, config)

    summary = {
        "dag_label": result.dag_label,
        "algorithm": result.algorithm,
        "total_nodes": result.total_nodes,
        "ff_chain_depth_raw": result.ff_chain_depth_raw,
        "ff_chain_depth_shifted": result.ff_chain_depth_shifted,
        "config": {
            "policy": config.policy.value,
            "issue_width": config.issue_width,
            "l_meas": config.l_meas,
            "l_ff": config.l_ff,
            "meas_width": config.meas_width,
            "ff_width": config.ff_width,
            "release_mode": config.release_mode.value,
        },
        "total_cycles": result.total_cycles,
        "throughput": round(result.throughput, 4),
        "stall_rate": round(result.stall_rate, 4),
        "utilization": round(result.utilization, 4),
    }
    json.dump(summary, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
