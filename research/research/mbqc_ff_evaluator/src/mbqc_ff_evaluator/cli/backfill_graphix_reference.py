from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from mbqc_ff_evaluator.adapters.graphix_reference import GraphixReferenceBackend
from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Backfill graphix-based reference depths into existing raw artifacts",
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
    parser.add_argument(
        "--max-logical-qubits",
        type=int,
        default=16,
        help="Only annotate artifacts up to this size",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing reference depths")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parents[3]
    raw_dir = args.raw_dir or base / "results" / "raw"
    repository = JsonArtifactRepository(raw_dir)
    backend = GraphixReferenceBackend(oneadapt_root=args.oneadapt_root)

    allowed_algorithms = None
    if args.algorithms is not None:
        allowed_algorithms = {Algorithm(name) for name in args.algorithms}

    updated = 0
    skipped_existing = 0
    skipped_filter = 0
    skipped_unavailable = 0

    for artifact in repository.load_artifacts():
        if artifact.status is not ArtifactStatus.SUCCESS:
            skipped_filter += 1
            continue
        if artifact.config.logical_qubits > args.max_logical_qubits:
            skipped_filter += 1
            continue
        if allowed_algorithms is not None and artifact.config.algorithm not in allowed_algorithms:
            skipped_filter += 1
            continue
        if artifact.depth_reference is not None and not args.force:
            skipped_existing += 1
            continue

        depth_reference = backend.compute_reference(artifact.config)
        if depth_reference is None:
            skipped_unavailable += 1
            continue
        repository.save_artifact(replace(artifact, depth_reference=depth_reference))
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
