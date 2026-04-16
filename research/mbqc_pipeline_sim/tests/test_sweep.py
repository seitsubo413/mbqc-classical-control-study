"""Tests for sweep and aggregate CLI."""
import csv
import json
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

    with open(out_csv) as f:
        rows = list(csv.DictReader(f))
    assert len(rows) > 0
    assert float(rows[0]["throughput"]) > 0
    assert rows[0]["dag_variant"] == "raw"

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

    with open(out_csv) as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    row = rows[0]
    assert row["algorithm"] == "QAOA"
    assert row["hardware_size"] == "4"
    assert row["logical_qubits"] == "16"
    assert row["dag_seed"] == "0"


@pytest.mark.smoke
def test_sweep_both_variants_and_comparison_output(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    artifact = {
        "config": {
            "algorithm": "TEST",
            "hardware_size": 4,
            "logical_qubits": 16,
            "seed": 0,
        },
        "ff_nodes": [
            {"node_id": 0, "phase": None, "node_type": "M"},
            {"node_id": 1, "phase": None, "node_type": "M"},
            {"node_id": 2, "phase": None, "node_type": "M"},
            {"node_id": 3, "phase": None, "node_type": "M"},
        ],
        "ff_edges": [
            {"src": 0, "dst": 1, "dependency": "x"},
            {"src": 1, "dst": 2, "dependency": "x"},
            {"src": 2, "dst": 3, "dependency": "x"},
        ],
        "ff_chain_depth_raw": 3,
        "ff_chain_depth_shifted": 1,
        "shifted_dependency_graph": {
            "nodes": [
                {"node_id": 0, "phase": None, "node_type": "M"},
                {"node_id": 1, "phase": None, "node_type": "M"},
                {"node_id": 2, "phase": None, "node_type": "M"},
                {"node_id": 3, "phase": None, "node_type": "M"},
            ],
            "edges": [
                {"src": 0, "dst": 2, "dependency": "x"},
                {"src": 1, "dst": 3, "dependency": "x"},
            ],
            "chain_depth": 1,
        },
    }
    (artifacts / "TEST_H4_Q16_seed0.json").write_text(json.dumps(artifact))

    sweep_csv = tmp_path / "sweep_variants.csv"
    sweep_main(
        [
            "--artifacts-dir", str(artifacts),
            "--output", str(sweep_csv),
            "--dag-variant", "both",
            "--issue-widths", "2",
            "--l-meas-values", "1",
            "--l-ff-values", "1",
            "--policies", "asap",
            "--release-modes", "next_cycle",
            "--meas-widths", "2",
            "--ff-widths", "2",
        ]
    )

    with open(sweep_csv) as f:
        sweep_rows = list(csv.DictReader(f))
    assert {row["dag_variant"] for row in sweep_rows} == {"raw", "shifted"}

    agg_csv = tmp_path / "agg_variants.csv"
    comparison_csv = tmp_path / "comparison.csv"
    agg_main(
        [
            "--input", str(sweep_csv),
            "--output", str(agg_csv),
            "--comparison-output", str(comparison_csv),
        ]
    )

    with open(comparison_csv) as f:
        comparison_rows = list(csv.DictReader(f))
    assert len(comparison_rows) == 1
    assert float(comparison_rows[0]["depth_reduction_pct"]) > 0.0
