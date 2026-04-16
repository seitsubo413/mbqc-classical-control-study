from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.adapters.oneadapt_backend import OneAdaptBackend
from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill shifted dependency-graph payloads into existing raw artifacts",
    )
    parser.add_argument("--raw-dir", type=Path, default=None)
    parser.add_argument("--oneadapt-root", type=Path, default=None)
    parser.add_argument(
        "--algorithms",
        nargs="+",
        default=None,
        choices=[algorithm.value for algorithm in Algorithm],
        help="Optional algorithm filter",
    )
    parser.add_argument("--hardware-sizes", nargs="+", type=int, default=None)
    parser.add_argument("--logical-qubits", nargs="+", type=int, default=None)
    parser.add_argument("--seeds", nargs="+", type=int, default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing shifted dependency-graph payloads",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parents[3]
    raw_dir = args.raw_dir or base / "results" / "raw"
    repository = JsonArtifactRepository(raw_dir)
    backend = OneAdaptBackend(oneadapt_root=args.oneadapt_root)

    allowed_algorithms = None if args.algorithms is None else {Algorithm(name) for name in args.algorithms}
    allowed_hardware = None if args.hardware_sizes is None else set(args.hardware_sizes)
    allowed_logical = None if args.logical_qubits is None else set(args.logical_qubits)
    allowed_seeds = None if args.seeds is None else set(args.seeds)

    updated = 0
    skipped_existing = 0
    skipped_filter = 0
    skipped_unavailable = 0

    for artifact in repository.load_artifacts():
        if artifact.status is not ArtifactStatus.SUCCESS:
            skipped_filter += 1
            continue
        if allowed_algorithms is not None and artifact.config.algorithm not in allowed_algorithms:
            skipped_filter += 1
            continue
        if allowed_hardware is not None and artifact.config.hardware_size not in allowed_hardware:
            skipped_filter += 1
            continue
        if allowed_logical is not None and artifact.config.logical_qubits not in allowed_logical:
            skipped_filter += 1
            continue
        if allowed_seeds is not None and artifact.config.seed not in allowed_seeds:
            skipped_filter += 1
            continue
        if artifact.shifted_dependency_graph is not None and not args.force:
            skipped_existing += 1
            continue

        _raw_snapshot, shifted_snapshot = backend.collect_dependency_snapshots(artifact.config)
        if shifted_snapshot is None:
            skipped_unavailable += 1
            continue

        repository.save_artifact(
            replace(
                artifact,
                ff_chain_depth_shifted=shifted_snapshot.chain_depth,
                shifted_dependency_graph=shifted_snapshot,
            )
        )
        updated += 1

    print(
        json.dumps(
            {
                "raw_dir": str(raw_dir),
                "updated": updated,
                "skipped_existing": skipped_existing,
                "skipped_filter": skipped_filter,
                "skipped_unavailable": skipped_unavailable,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
