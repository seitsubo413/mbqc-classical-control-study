from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Sequence

STUDY_ID = "13_shifted_dag_dynamic"
ARTIFACT_SET_ID = "common_coupled_subset"
PIPELINE_EXPERIMENT_ID = "raw_vs_shifted_next_cycle_width_matched"
ALGORITHMS = ("QAOA", "QFT", "VQE")
HQ_PAIRS = ((4, 16), (6, 36), (8, 64))
SEEDS = (0, 1, 2, 3, 4)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare namespaced directories for the shifted-DAG dynamic study",
    )
    parser.add_argument("--source-raw-dir", type=Path, default=None)
    parser.add_argument("--ff-study-dir", type=Path, default=None)
    parser.add_argument("--pipeline-study-dir", type=Path, default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite already-copied artifacts and manifest files",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[5]
    source_raw_dir = args.source_raw_dir or (
        repo_root / "research" / "mbqc_ff_evaluator" / "results" / "raw"
    )
    ff_study_dir = args.ff_study_dir or (
        repo_root
        / "research"
        / "mbqc_ff_evaluator"
        / "results"
        / "studies"
        / STUDY_ID
        / ARTIFACT_SET_ID
    )
    pipeline_study_dir = args.pipeline_study_dir or (
        repo_root
        / "research"
        / "mbqc_pipeline_sim"
        / "results"
        / "studies"
        / STUDY_ID
        / PIPELINE_EXPERIMENT_ID
    )

    ff_artifacts_dir = ff_study_dir / "artifacts"
    ff_summary_dir = ff_study_dir / "summary"
    ff_logs_dir = ff_study_dir / "logs"
    pipeline_summary_dir = pipeline_study_dir / "summary"
    pipeline_figures_dir = pipeline_study_dir / "figures"
    pipeline_logs_dir = pipeline_study_dir / "logs"

    for directory in (
        ff_artifacts_dir,
        ff_summary_dir,
        ff_logs_dir,
        pipeline_summary_dir,
        pipeline_figures_dir,
        pipeline_logs_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    copied = 0
    overwritten = 0
    selected_filenames: list[str] = []
    for src_path in sorted(source_raw_dir.glob("*.json")):
        payload = json.loads(src_path.read_text(encoding="utf-8"))
        if not _matches_study_subset(payload):
            continue
        dst_path = ff_artifacts_dir / src_path.name
        if dst_path.exists():
            if not args.force:
                selected_filenames.append(dst_path.name)
                continue
            overwritten += 1
        shutil.copy2(src_path, dst_path)
        copied += 1
        selected_filenames.append(dst_path.name)

    manifest = {
        "study_id": STUDY_ID,
        "artifact_set_id": ARTIFACT_SET_ID,
        "pipeline_experiment_id": PIPELINE_EXPERIMENT_ID,
        "source_raw_dir": str(source_raw_dir),
        "ff_study_dir": str(ff_study_dir),
        "pipeline_study_dir": str(pipeline_study_dir),
        "filters": {
            "algorithms": list(ALGORITHMS),
            "hq_pairs": [f"{hardware}:{logical}" for hardware, logical in HQ_PAIRS],
            "seeds": list(SEEDS),
        },
        "paths": {
            "ff_artifacts_dir": str(ff_artifacts_dir),
            "ff_summary_dir": str(ff_summary_dir),
            "ff_logs_dir": str(ff_logs_dir),
            "pipeline_summary_dir": str(pipeline_summary_dir),
            "pipeline_figures_dir": str(pipeline_figures_dir),
            "pipeline_logs_dir": str(pipeline_logs_dir),
            "pipeline_sweep_csv": str(pipeline_summary_dir / "sweep.csv"),
            "pipeline_aggregated_csv": str(pipeline_summary_dir / "aggregated.csv"),
            "pipeline_comparison_csv": str(pipeline_summary_dir / "comparison.csv"),
        },
        "selected_artifacts": selected_filenames,
    }

    manifest_path = ff_study_dir / "manifest.json"
    pipeline_manifest_path = pipeline_study_dir / "manifest.json"
    if args.force or not manifest_path.exists():
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.force or not pipeline_manifest_path.exists():
        pipeline_manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "study_id": STUDY_ID,
                "artifact_set_id": ARTIFACT_SET_ID,
                "pipeline_experiment_id": PIPELINE_EXPERIMENT_ID,
                "copied": copied,
                "overwritten": overwritten,
                "selected_count": len(selected_filenames),
                "ff_study_dir": str(ff_study_dir),
                "pipeline_study_dir": str(pipeline_study_dir),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _matches_study_subset(payload: dict[str, Any]) -> bool:
    config = payload.get("config", {})
    algorithm = str(config.get("algorithm", ""))
    hardware_size = int(config.get("hardware_size", -1))
    logical_qubits = int(config.get("logical_qubits", -1))
    seed = int(config.get("seed", -1))
    if algorithm not in ALGORITHMS:
        return False
    if (hardware_size, logical_qubits) not in HQ_PAIRS:
        return False
    return seed in SEEDS


if __name__ == "__main__":
    raise SystemExit(main())
