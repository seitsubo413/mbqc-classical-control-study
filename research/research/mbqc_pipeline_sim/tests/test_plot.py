from pathlib import Path

import pytest

from mbqc_pipeline_sim.visualization.plots import plot_all


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
    if not sweep_csv.exists():
        pytest.skip("Sweep CSV not found")

    plot_all(
        sweep_csv,
        tmp_path,
        conservative_csv=conservative_csv,
        conservative_meas_csv=conservative_meas_csv,
    )

    assert (tmp_path / "fig1_throughput_vs_width.png").exists()
    assert (tmp_path / "fig5_feasibility.png").exists()
    if conservative_csv.exists():
        assert (tmp_path / "fig6_conservative_alignment.png").exists()
        assert (tmp_path / "fig7_ff_underprovisioning.png").exists()
    if conservative_meas_csv.exists():
        assert (tmp_path / "fig8_stage_width_comparison.png").exists()
