"""Tests for sweep and aggregate CLI."""
from pathlib import Path

import pytest

from mbqc_pipeline_sim.cli.sweep import main as sweep_main
from mbqc_pipeline_sim.cli.aggregate import main as agg_main


@pytest.mark.smoke
def test_sweep_small(tmp_path: Path) -> None:
    artifacts = (
        Path(__file__).resolve().parents[2]
        / "mbqc_ff_evaluator"
        / "results"
        / "raw"
    )
    if not artifacts.exists():
        pytest.skip("FF evaluator artifacts not found")

    out_csv = tmp_path / "sweep.csv"
    sweep_main(
        [
            "--artifacts-dir", str(artifacts),
            "--output", str(out_csv),
            "--issue-widths", "1,4",
            "--l-meas-values", "1",
            "--l-ff-values", "1,2",
            "--policies", "asap,greedy_critical",
            "--algorithms", "QAOA",
        ]
    )
    assert out_csv.exists()

    import csv
    with open(out_csv) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) > 0
    assert float(rows[0]["throughput"]) > 0

    agg_csv = tmp_path / "aggregated.csv"
    agg_main(["--input", str(out_csv), "--output", str(agg_csv)])
    assert agg_csv.exists()
    with open(agg_csv) as f:
        agg_rows = list(csv.DictReader(f))
    assert len(agg_rows) > 0


@pytest.mark.smoke
def test_sweep_filters_to_specific_seed_and_pair(tmp_path: Path) -> None:
    artifacts = (
        Path(__file__).resolve().parents[2]
        / "mbqc_ff_evaluator"
        / "results"
        / "raw"
    )
    if not artifacts.exists():
        pytest.skip("FF evaluator artifacts not found")

    out_csv = tmp_path / "filtered_sweep.csv"
    sweep_main(
        [
            "--artifacts-dir", str(artifacts),
            "--output", str(out_csv),
            "--issue-widths", "1",
            "--l-meas-values", "1",
            "--l-ff-values", "1",
            "--policies", "asap",
            "--algorithms", "QAOA",
            "--dag-seeds", "0",
            "--hq-pairs", "4:16",
        ]
    )

    import csv
    with open(out_csv) as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    row = rows[0]
    assert row["algorithm"] == "QAOA"
    assert row["hardware_size"] == "4"
    assert row["logical_qubits"] == "16"
    assert row["dag_seed"] == "0"
