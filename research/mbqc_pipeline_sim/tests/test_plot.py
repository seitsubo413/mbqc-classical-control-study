import csv
from pathlib import Path

import pytest

from mbqc_pipeline_sim.visualization.plots import (
    plot_all,
    plot_fig9_shifted_throughput_comparison,
    plot_fig10_shifted_stall_comparison,
    plot_fig11_depth_reduction_vs_throughput_gain,
)


@pytest.mark.smoke
def test_plot_all_smoke(tmp_path: Path) -> None:
    sweep_csv = Path(__file__).resolve().parent.parent / "results" / "summary" / "sweep.csv"
    conservative_csv = (
        Path(__file__).resolve().parent.parent
        / "results"
        / "summary"
        / "sweep_conservative_common.csv"
    )
    conservative_meas_csv = (
        Path(__file__).resolve().parent.parent
        / "results"
        / "summary"
        / "sweep_conservative_meas_common.csv"
    )
    comparison_csv = (
        Path(__file__).resolve().parent.parent
        / "results"
        / "summary"
        / "shifted_comparison.csv"
    )
    if not sweep_csv.exists():
        pytest.skip("Sweep CSV not found")

    plot_all(
        sweep_csv,
        tmp_path,
        conservative_csv=conservative_csv,
        conservative_meas_csv=conservative_meas_csv,
        comparison_csv=comparison_csv,
    )

    assert (tmp_path / "fig1_throughput_vs_width.png").exists()
    assert (tmp_path / "fig5_feasibility.png").exists()
    if conservative_csv.exists():
        assert (tmp_path / "fig6_conservative_alignment.png").exists()
        assert (tmp_path / "fig7_ff_underprovisioning.png").exists()
    if conservative_meas_csv.exists():
        assert (tmp_path / "fig8_stage_width_comparison.png").exists()
    if comparison_csv.exists():
        assert (tmp_path / "fig9_shifted_throughput_comparison.png").exists()
        assert (tmp_path / "fig10_shifted_stall_comparison.png").exists()
        assert (tmp_path / "fig11_depth_reduction_vs_throughput_gain.png").exists()


@pytest.mark.smoke
def test_shifted_comparison_plots_smoke(tmp_path: Path) -> None:
    comparison_csv = tmp_path / "shifted_comparison.csv"
    fieldnames = [
        "algorithm",
        "hardware_size",
        "logical_qubits",
        "policy",
        "release_mode",
        "issue_width",
        "l_meas",
        "l_ff",
        "meas_width",
        "ff_width",
        "n_seeds_raw",
        "n_seeds_shifted",
        "ff_chain_depth_raw_median",
        "ff_chain_depth_shifted_median",
        "depth_reduction_pct",
        "throughput_raw_median",
        "throughput_shifted_median",
        "throughput_delta",
        "throughput_gain_pct",
        "stall_rate_raw_median",
        "stall_rate_shifted_median",
        "stall_rate_delta",
        "stall_reduction_pct",
        "utilization_raw_median",
        "utilization_shifted_median",
        "utilization_delta",
        "utilization_gain_pct",
    ]

    rows = []
    for algorithm in ("QAOA", "QFT", "VQE"):
        for hardware_size, logical_qubits in (("4", "16"), ("6", "36"), ("8", "64")):
            rows.append(
                {
                    "algorithm": algorithm,
                    "hardware_size": hardware_size,
                    "logical_qubits": logical_qubits,
                    "policy": "asap",
                    "release_mode": "next_cycle",
                    "issue_width": "4",
                    "l_meas": "1",
                    "l_ff": "1",
                    "meas_width": "4",
                    "ff_width": "4",
                    "n_seeds_raw": "5",
                    "n_seeds_shifted": "5",
                    "ff_chain_depth_raw_median": "20",
                    "ff_chain_depth_shifted_median": "5",
                    "depth_reduction_pct": "75",
                    "throughput_raw_median": "0.4",
                    "throughput_shifted_median": "0.6",
                    "throughput_delta": "0.2",
                    "throughput_gain_pct": "50",
                    "stall_rate_raw_median": "0.3",
                    "stall_rate_shifted_median": "0.1",
                    "stall_rate_delta": "-0.2",
                    "stall_reduction_pct": "66.7",
                    "utilization_raw_median": "0.4",
                    "utilization_shifted_median": "0.6",
                    "utilization_delta": "0.2",
                    "utilization_gain_pct": "50",
                }
            )

    with comparison_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    plot_fig9_shifted_throughput_comparison(comparison_csv, tmp_path)
    plot_fig10_shifted_stall_comparison(comparison_csv, tmp_path)
    plot_fig11_depth_reduction_vs_throughput_gain(comparison_csv, tmp_path)

    assert (tmp_path / "fig9_shifted_throughput_comparison.png").exists()
    assert (tmp_path / "fig10_shifted_stall_comparison.png").exists()
    assert (tmp_path / "fig11_depth_reduction_vs_throughput_gain.png").exists()
