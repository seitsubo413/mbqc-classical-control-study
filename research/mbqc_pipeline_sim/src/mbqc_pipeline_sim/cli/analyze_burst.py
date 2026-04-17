"""CLI: Ready-burst analysis — cycle-level ready_queue_size raw vs shifted (Option 1)."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from mbqc_pipeline_sim.adapters.artifact_loader import load_dag_from_json
from mbqc_pipeline_sim.core.simulator import MbqcPipelineSimulator
from mbqc_pipeline_sim.domain.enums import DagVariant, ReleaseMode, SchedulingPolicy
from mbqc_pipeline_sim.domain.models import PipelineConfig


# Representative (artifact_path, label) pairs to analyse
_DEFAULT_CASES = [
    ("QAOA_H8_Q64_seed0.json", "QAOA H8/Q64"),
    ("QFT_H6_Q36_seed0.json",  "QFT H6/Q36"),
    ("QFT_H4_Q16_seed0.json",  "QFT H4/Q16"),
    ("VQE_H8_Q64_seed0.json",  "VQE H8/Q64"),
]

_POLICIES = ["asap", "greedy_critical"]


def _run_one(
    artifact: Path,
    dag_variant: DagVariant,
    policy: str,
    issue_width: int,
    l_meas: int,
    l_ff: int,
    meas_width: int,
    ff_width: int,
) -> list[dict[str, object]]:
    dag = load_dag_from_json(artifact, dag_variant=dag_variant)
    config = PipelineConfig(
        issue_width=issue_width,
        l_meas=l_meas,
        l_ff=l_ff,
        meas_width=meas_width,
        ff_width=ff_width,
        release_mode=ReleaseMode.NEXT_CYCLE,
        policy=SchedulingPolicy(policy),
    )
    result = MbqcPipelineSimulator().run(dag, config)
    rows = []
    for rec in result.cycle_records:
        rows.append(
            {
                "algorithm": dag.algorithm,
                "hardware_size": dag.hardware_size,
                "logical_qubits": dag.logical_qubits,
                "dag_seed": dag.dag_seed,
                "dag_variant": dag_variant.value,
                "policy": policy,
                "ff_chain_depth": dag.ff_chain_depth,
                "ff_chain_depth_raw": dag.ff_chain_depth_raw,
                "ff_chain_depth_shifted": dag.ff_chain_depth_shifted
                if dag.ff_chain_depth_shifted is not None
                else "",
                "cycle": rec.cycle,
                "issued": rec.issued,
                "ready_queue_size": rec.ready_queue_size,
                "waiting_ff_queue_size": rec.waiting_ff_queue_size,
                "in_flight_meas": rec.in_flight_meas,
                "in_flight_ff": rec.in_flight_ff,
                "total_done": rec.total_done,
                "total_nodes": result.total_nodes,
                "total_cycles": result.total_cycles,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Collect cycle-level ready_queue_size for burst analysis"
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        required=True,
        help="Directory containing FF-evaluator JSON artifacts",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "results"
        / "studies"
        / "burst_analysis",
    )
    parser.add_argument("--issue-width", type=int, default=8)
    parser.add_argument("--l-meas", type=int, default=1)
    parser.add_argument("--l-ff", type=int, default=2)
    parser.add_argument("--meas-width", type=int, default=8)
    parser.add_argument("--ff-width", type=int, default=4)
    args = parser.parse_args(argv)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, object]] = []

    for filename, label in _DEFAULT_CASES:
        artifact = args.artifacts_dir / filename
        if not artifact.exists():
            print(f"  SKIP (not found): {artifact}")
            continue
        for dag_variant in [DagVariant.RAW, DagVariant.SHIFTED]:
            for policy in _POLICIES:
                try:
                    rows = _run_one(
                        artifact,
                        dag_variant,
                        policy,
                        args.issue_width,
                        args.l_meas,
                        args.l_ff,
                        args.meas_width,
                        args.ff_width,
                    )
                    all_rows.extend(rows)
                    print(
                        f"  OK  {label} {dag_variant.value:8s} {policy:25s} "
                        f"→ {len(rows)} cycles"
                    )
                except Exception as exc:
                    print(f"  ERR {label} {dag_variant.value} {policy}: {exc}")

    out_csv = args.output_dir / "cycle_records.csv"
    if all_rows:
        with out_csv.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nSaved {len(all_rows)} cycle records → {out_csv}")
    else:
        print("No data collected.")


if __name__ == "__main__":
    main()
