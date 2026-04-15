from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import median
from typing import Any, Sequence

from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.adapters.oneadapt_backend import OneAdaptBackend
from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus
from mbqc_ff_evaluator.domain.models import ExperimentConfig
from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService

TIMEOUT_MEDIAN_SEC = 600.0
CONSECUTIVE_TIMEOUT_LIMIT = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run sweep experiments for MBQC FF evaluator")
    parser.add_argument(
        "--algorithms",
        nargs="+",
        required=True,
        choices=[a.value for a in Algorithm],
    )
    parser.add_argument("--hardware-sizes", nargs="+", type=int, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    parser.add_argument("--refresh-bound", type=int, default=20)
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--coupled", action="store_true", help="Use Q=H^2 coupled mode (Sweep A)")
    parser.add_argument(
        "--logical-qubits",
        type=int,
        default=None,
        help="Fixed Q for Sweep B (overrides coupled H^2)",
    )
    parser.add_argument("--oneadapt-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--verbose-oneadapt", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    output_dir = args.output_dir or _default_output_dir()
    backend = OneAdaptBackend(
        oneadapt_root=args.oneadapt_root,
        verbose=args.verbose_oneadapt,
    )
    repository = JsonArtifactRepository(output_dir)
    service = ArtifactCollectionService(compiler_backend=backend, repository=repository)

    refresh = not args.no_refresh
    algorithms = [Algorithm(a) for a in args.algorithms]
    total_cases = 0
    total_success = 0
    total_skipped = 0

    for algo in algorithms:
        consecutive_timeout_h = 0
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"Algorithm: {algo.value}", file=sys.stderr)
        print(f"{'=' * 60}", file=sys.stderr)

        for h in args.hardware_sizes:
            q = _resolve_q(args, h)
            elapsed_list: list[float] = []
            statuses: list[ArtifactStatus] = []

            print(f"\n  H={h}, Q={q}", file=sys.stderr)
            for seed in args.seeds:
                config = ExperimentConfig(
                    algorithm=algo,
                    hardware_size=h,
                    logical_qubits=q,
                    seed=seed,
                    refresh=refresh,
                    refresh_bound=args.refresh_bound,
                )
                total_cases += 1
                t0 = time.perf_counter()
                try:
                    record = service.collect(config)
                    wall = time.perf_counter() - t0
                    elapsed_list.append(wall)
                    statuses.append(record.artifact.status)
                    status_str = record.artifact.status.value
                    depth_str = str(record.artifact.ff_chain_depth_raw)
                    if record.artifact.status == ArtifactStatus.SUCCESS:
                        total_success += 1
                    print(
                        f"    seed={seed}  status={status_str}  "
                        f"depth_raw={depth_str}  {wall:.1f}s  -> {record.artifact_path.name}",
                        file=sys.stderr,
                    )
                except Exception as exc:
                    wall = time.perf_counter() - t0
                    elapsed_list.append(wall)
                    statuses.append(ArtifactStatus.EXCEPTION)
                    print(
                        f"    seed={seed}  EXCEPTION  {wall:.1f}s  {exc!r}",
                        file=sys.stderr,
                    )

            all_timeout = all(s == ArtifactStatus.TIMEOUT_GUARD for s in statuses)
            med_elapsed = median(elapsed_list) if elapsed_list else 0.0

            if all_timeout:
                consecutive_timeout_h += 1
                print(
                    f"  -> All seeds timed out ({consecutive_timeout_h}/{CONSECUTIVE_TIMEOUT_LIMIT})",
                    file=sys.stderr,
                )
            else:
                consecutive_timeout_h = 0

            if consecutive_timeout_h >= CONSECUTIVE_TIMEOUT_LIMIT:
                print(
                    f"  STOP: {CONSECUTIVE_TIMEOUT_LIMIT} consecutive H values all timed out.",
                    file=sys.stderr,
                )
                total_skipped += len(args.seeds) * (
                    len(args.hardware_sizes) - args.hardware_sizes.index(h) - 1
                )
                break

            if med_elapsed > TIMEOUT_MEDIAN_SEC:
                print(
                    f"  STOP: Median elapsed {med_elapsed:.0f}s exceeds {TIMEOUT_MEDIAN_SEC:.0f}s limit.",
                    file=sys.stderr,
                )
                total_skipped += len(args.seeds) * (
                    len(args.hardware_sizes) - args.hardware_sizes.index(h) - 1
                )
                break

    summary: dict[str, Any] = {
        "total_cases": total_cases,
        "success": total_success,
        "skipped_remaining": total_skipped,
        "output_dir": str(output_dir),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def _resolve_q(args: argparse.Namespace, h: int) -> int:
    if args.logical_qubits is not None:
        return int(args.logical_qubits)
    if args.coupled:
        return h * h
    return h * h


def _default_output_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "results" / "raw"


if __name__ == "__main__":
    raise SystemExit(main())
