from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.analysis.outliers import analyze_measurement_delay_groups


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze measurement-delay outliers from raw artifacts")
    parser.add_argument("--raw-dir", type=Path, default=None)
    parser.add_argument("--summary-dir", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parents[3]
    raw_dir = args.raw_dir or base / "results" / "raw"
    summary_dir = args.summary_dir or base / "results" / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)

    repository = JsonArtifactRepository(raw_dir)
    artifacts = repository.load_artifacts()
    group_rows, outlier_rows = analyze_measurement_delay_groups(artifacts)

    group_path = summary_dir / "measurement_delay_group_summary.csv"
    outlier_path = summary_dir / "measurement_delay_outliers.csv"

    _write_rows(group_path, group_rows)
    _write_rows(outlier_path, outlier_rows)

    print(
        json.dumps(
            {
                "group_summary": str(group_path),
                "outliers": str(outlier_path),
                "n_groups": len(group_rows),
                "n_outliers": len(outlier_rows),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _write_rows(path: Path, rows: Sequence[Any]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    header = list(asdict(rows[0]).keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


if __name__ == "__main__":
    raise SystemExit(main())
