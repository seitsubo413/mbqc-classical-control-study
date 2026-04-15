"""End-to-end pipeline test: aggregate raw JSONs → CSV → figures.

Run after sweep experiments have populated results/raw/:
    pytest tests/test_pipeline.py -v
    pytest -m pipeline -v
"""

from __future__ import annotations

import pytest
from pathlib import Path

from tests.helpers import RESULTS_FIGURES, RESULTS_RAW, RESULTS_SUMMARY


@pytest.mark.pipeline
class TestAggregatePipeline:

    def test_aggregate_produces_csvs(self) -> None:
        from mbqc_ff_evaluator.cli.aggregate import main as aggregate_main

        ret = aggregate_main([
            "--raw-dir", str(RESULTS_RAW),
            "--summary-dir", str(RESULTS_SUMMARY),
        ])
        assert ret == 0

        metrics = RESULTS_SUMMARY / "metrics.csv"
        budgets = RESULTS_SUMMARY / "budgets.csv"
        assert metrics.exists(), "metrics.csv was not created"
        assert budgets.exists(), "budgets.csv was not created"
        assert metrics.stat().st_size > 100, "metrics.csv is suspiciously small"
        assert budgets.stat().st_size > 100, "budgets.csv is suspiciously small"

        lines = metrics.read_text().strip().splitlines()
        n_data_rows = len(lines) - 1
        assert n_data_rows >= 1, f"metrics.csv has {n_data_rows} data rows"
        print(f"\n  metrics.csv: {n_data_rows} rows")

        budget_lines = budgets.read_text().strip().splitlines()
        n_budget_rows = len(budget_lines) - 1
        assert n_budget_rows >= 1, f"budgets.csv has {n_budget_rows} data rows"
        print(f"  budgets.csv: {n_budget_rows} rows")

    def test_plot_produces_figures(self) -> None:
        from mbqc_ff_evaluator.cli.plot import main as plot_main

        ret = plot_main([
            "--summary-dir", str(RESULTS_SUMMARY),
            "--output-dir", str(RESULTS_FIGURES),
            "--format", "png",
        ])
        assert ret == 0

        expected_files = [
            "fig1_divergence.png",
            "fig2_budget.png",
            "fig3_bottlenecks.png",
            "fig4_shifted_budget.png",
            "fig5_sensitivity.png",
            "fig6_reference_depth.png",
            "fig7_hardware_width.png",
            "appendix_conservative.png",
        ]
        for fname in expected_files:
            fpath = RESULTS_FIGURES / fname
            assert fpath.exists(), f"{fname} was not created"
            assert fpath.stat().st_size > 1000, f"{fname} is suspiciously small"

        print(f"\n  Generated {len(expected_files)} figures in {RESULTS_FIGURES}")

    def test_plot_pdf_format(self) -> None:
        from mbqc_ff_evaluator.cli.plot import main as plot_main

        pdf_dir = RESULTS_FIGURES / "pdf"
        ret = plot_main([
            "--summary-dir", str(RESULTS_SUMMARY),
            "--output-dir", str(pdf_dir),
            "--format", "pdf",
        ])
        assert ret == 0
        assert (pdf_dir / "fig1_divergence.pdf").exists()
        assert (pdf_dir / "fig2_budget.pdf").exists()
        assert (pdf_dir / "fig3_bottlenecks.pdf").exists()
        assert (pdf_dir / "fig6_reference_depth.pdf").exists()
        assert (pdf_dir / "fig7_hardware_width.pdf").exists()
        print(f"\n  PDF figures in {pdf_dir}")
