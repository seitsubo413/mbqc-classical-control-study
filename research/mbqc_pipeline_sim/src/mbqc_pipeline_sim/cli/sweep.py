"""CLI: Run parameter sweep across pipeline configurations and DAGs."""
from __future__ import annotations

import argparse
from dataclasses import replace
import itertools
import sys
import time
from pathlib import Path

from mbqc_pipeline_sim.adapters.artifact_loader import load_all_dags
from mbqc_pipeline_sim.adapters.csv_writer import write_results
from mbqc_pipeline_sim.core.simulator import MbqcPipelineSimulator
from mbqc_pipeline_sim.domain.enums import ReleaseMode, SchedulingPolicy
from mbqc_pipeline_sim.domain.models import PipelineConfig, SimResult


def _parse_csv_ints(raw: str) -> set[int]:
    return {int(token.strip()) for token in raw.split(",") if token.strip()}


def _parse_hq_pairs(raw: str) -> set[tuple[int, int]]:
    pairs: set[tuple[int, int]] = set()
    for token in raw.split(","):
        value = token.strip()
        if not value:
            continue
        hardware_size, logical_qubits = value.split(":", maxsplit=1)
        pairs.add((int(hardware_size), int(logical_qubits)))
    return pairs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pipeline-sim parameter sweep")
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path(__file__).resolve().parents[4]
        / "mbqc_ff_evaluator"
        / "results"
        / "raw",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "results" / "summary" / "sweep.csv",
    )
    parser.add_argument(
        "--issue-widths",
        type=str,
        default="1,2,4,8,16",
        help="Comma-separated issue widths",
    )
    parser.add_argument(
        "--l-meas-values",
        type=str,
        default="1,2,3",
        help="Comma-separated L_meas values",
    )
    parser.add_argument(
        "--l-ff-values",
        type=str,
        default="1,2,3,5",
        help="Comma-separated L_ff values",
    )
    parser.add_argument(
        "--policies",
        type=str,
        default="asap,layer,greedy_critical,random",
        help="Comma-separated policy names",
    )
    parser.add_argument(
        "--release-modes",
        type=str,
        default=ReleaseMode.SAME_CYCLE.value,
        help="Comma-separated release modes",
    )
    parser.add_argument(
        "--meas-widths",
        type=str,
        default="",
        help="Comma-separated measurement stage widths (empty=unlimited)",
    )
    parser.add_argument(
        "--ff-widths",
        type=str,
        default="",
        help="Comma-separated FF stage widths (empty=unlimited)",
    )
    parser.add_argument(
        "--algorithms",
        type=str,
        default="",
        help="Filter artifacts to specific algorithms (comma-separated, empty=all)",
    )
    parser.add_argument(
        "--dag-seeds",
        type=str,
        default="",
        help="Filter artifacts to specific DAG seeds (comma-separated, empty=all)",
    )
    parser.add_argument(
        "--hardware-sizes",
        type=str,
        default="",
        help="Filter artifacts to specific hardware sizes (comma-separated, empty=all)",
    )
    parser.add_argument(
        "--logical-qubits",
        type=str,
        default="",
        help="Filter artifacts to specific logical qubit counts (comma-separated, empty=all)",
    )
    parser.add_argument(
        "--hq-pairs",
        type=str,
        default="",
        help="Filter artifacts to specific H:Q pairs (comma-separated, e.g. 4:16,6:36)",
    )
    args = parser.parse_args(argv)

    issue_widths = [int(x) for x in args.issue_widths.split(",")]
    l_meas_values = [int(x) for x in args.l_meas_values.split(",")]
    l_ff_values = [int(x) for x in args.l_ff_values.split(",")]
    policies = [SchedulingPolicy(x.strip()) for x in args.policies.split(",")]
    release_modes = [ReleaseMode(x.strip()) for x in args.release_modes.split(",")]
    algo_filter = {a.strip() for a in args.algorithms.split(",") if a.strip()}
    seed_filter = _parse_csv_ints(args.dag_seeds)
    hardware_filter = _parse_csv_ints(args.hardware_sizes)
    logical_filter = _parse_csv_ints(args.logical_qubits)
    hq_pair_filter = _parse_hq_pairs(args.hq_pairs)

    def _parse_optional_widths(raw: str) -> list[int | None]:
        values = [token.strip() for token in raw.split(",") if token.strip()]
        return [None] if not values else [int(value) for value in values]

    meas_widths = _parse_optional_widths(args.meas_widths)
    ff_widths = _parse_optional_widths(args.ff_widths)

    dags = load_all_dags(args.artifacts_dir)
    if algo_filter:
        dags = [d for d in dags if d.algorithm in algo_filter]
    if seed_filter:
        dags = [d for d in dags if d.dag_seed in seed_filter]
    if hardware_filter:
        dags = [d for d in dags if d.hardware_size in hardware_filter]
    if logical_filter:
        dags = [d for d in dags if d.logical_qubits in logical_filter]
    if hq_pair_filter:
        dags = [d for d in dags if (d.hardware_size, d.logical_qubits) in hq_pair_filter]

    if not dags:
        print("No DAG artifacts found.", file=sys.stderr)
        sys.exit(1)

    configs = [
        PipelineConfig(
            issue_width=w,
            l_meas=lm,
            l_ff=lf,
            meas_width=mw,
            ff_width=fw,
            release_mode=rm,
            policy=p,
        )
        for w, lm, lf, p, rm, mw, fw in itertools.product(
            issue_widths,
            l_meas_values,
            l_ff_values,
            policies,
            release_modes,
            meas_widths,
            ff_widths,
        )
    ]

    total = len(dags) * len(configs)
    print(f"Sweep: {len(dags)} DAGs × {len(configs)} configs = {total} runs")

    sim = MbqcPipelineSimulator()
    results: list[SimResult] = []
    t0 = time.perf_counter()

    for i, (dag, cfg) in enumerate(itertools.product(dags, configs)):
        run_cfg = cfg if cfg.policy != SchedulingPolicy.RANDOM else replace(cfg, seed=dag.dag_seed)
        result = sim.run(dag, run_cfg)
        results.append(result)
        if (i + 1) % 500 == 0 or (i + 1) == total:
            elapsed = time.perf_counter() - t0
            rate = (i + 1) / elapsed
            eta = (total - i - 1) / rate if rate > 0 else 0
            print(
                f"  [{i+1}/{total}] {elapsed:.1f}s elapsed, ~{eta:.0f}s remaining",
                flush=True,
            )

    write_results(results, args.output)
    elapsed = time.perf_counter() - t0
    print(f"Done: {len(results)} results → {args.output}  ({elapsed:.1f}s)")


if __name__ == "__main__":
    main()
