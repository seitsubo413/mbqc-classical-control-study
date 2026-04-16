import csv
from pathlib import Path

from mbqc_pipeline_sim.analysis.shifted_study import (
    build_paired_seed_effects,
    build_shifted_study_outputs,
    read_sweep_observations,
)
from mbqc_pipeline_sim.cli.analyze_shifted_study import main as analyze_main


def test_shifted_study_outputs(tmp_path: Path) -> None:
    sweep_csv = tmp_path / "sweep.csv"
    _write_sweep_csv(
        sweep_csv,
        [
            _row("raw", "TESTA", 4, 16, 0, 10, 4, 1.0, 0.2, 0.5),
            _row("shifted", "TESTA", 4, 16, 0, 4, 4, 1.5, 0.1, 0.75),
            _row("raw", "TESTA", 4, 16, 0, 10, 4, 1.0, 0.2, 0.5, ff_width=8),
            _row("shifted", "TESTA", 4, 16, 0, 4, 4, 1.5, 0.1, 0.75, ff_width=8),
            _row("raw", "TESTA", 4, 16, 1, 10, 4, 2.0, 0.0, 1.0),
            _row("shifted", "TESTA", 4, 16, 1, 4, 4, 2.0, 0.0, 1.0),
            _row("raw", "TESTA", 4, 16, 1, 10, 4, 2.0, 0.0, 1.0, ff_width=8),
            _row("shifted", "TESTA", 4, 16, 1, 4, 4, 2.0, 0.0, 1.0, ff_width=8),
            _row("raw", "TESTA", 4, 16, 2, 10, 4, 1.25, 0.05, 0.625),
            _row(
                "raw",
                "TESTB",
                6,
                36,
                0,
                8,
                2,
                1.0,
                0.25,
                0.5,
                issue_width=8,
                l_meas=2,
                l_ff=2,
                meas_width=8,
                ff_width=8,
            ),
            _row(
                "shifted",
                "TESTB",
                6,
                36,
                0,
                2,
                2,
                1.1,
                0.1,
                0.55,
                issue_width=8,
                l_meas=2,
                l_ff=2,
                meas_width=8,
                ff_width=8,
            ),
            _row(
                "raw",
                "TESTB",
                6,
                36,
                0,
                8,
                2,
                1.0,
                0.25,
                0.5,
                issue_width=8,
                l_meas=2,
                l_ff=2,
                meas_width=8,
                ff_width=4,
            ),
            _row(
                "shifted",
                "TESTB",
                6,
                36,
                0,
                2,
                2,
                1.1,
                0.3,
                0.55,
                issue_width=8,
                l_meas=2,
                l_ff=2,
                meas_width=8,
                ff_width=4,
            ),
            _row(
                "raw",
                "TESTB",
                6,
                36,
                0,
                8,
                2,
                0.95,
                0.27,
                0.48,
                policy="greedy_critical",
                issue_width=8,
                l_meas=2,
                l_ff=2,
                meas_width=8,
                ff_width=4,
            ),
            _row(
                "shifted",
                "TESTB",
                6,
                36,
                0,
                2,
                2,
                1.3,
                0.09,
                0.6,
                policy="greedy_critical",
                issue_width=8,
                l_meas=2,
                l_ff=2,
                meas_width=8,
                ff_width=4,
            ),
        ],
    )

    observations = read_sweep_observations(sweep_csv)
    effects = build_paired_seed_effects(observations)
    outputs = build_shifted_study_outputs(observations)

    assert len(effects) == 7
    assert outputs.paired_seed_effects[0]["raw_stall_bucket"] == "stall_high"
    assert outputs.paired_seed_effects[0]["latency_profile"] == "l1_l1"
    assert outputs.paired_seed_effects[-1]["width_profile"] == "W8_M8_F8"

    algorithm_summary = {row["algorithm"]: row for row in outputs.algorithm_summary}
    assert algorithm_summary["TESTA"]["pair_count"] == 4
    assert algorithm_summary["TESTA"]["throughput_positive_count"] == 2
    assert algorithm_summary["TESTA"]["throughput_zero_count"] == 2
    assert algorithm_summary["TESTA"]["throughput_negative_count"] == 0
    assert algorithm_summary["TESTA"]["throughput_gain_pct_median"] == 25.0

    policy_latency_rows = {
        (row["algorithm"], row["policy"], row["latency_profile"]): row
        for row in outputs.policy_latency_summary
    }
    assert policy_latency_rows[("TESTB", "asap", "l2_l2")]["pair_count"] == 2

    policy_saturation_rows = {
        (row["algorithm"], row["policy"], row["raw_saturation_bucket"]): row
        for row in outputs.policy_saturation_summary
    }
    assert policy_saturation_rows[("TESTA", "asap", "active")]["throughput_zero_count"] == 2

    policy_width_rows = {
        (row["algorithm"], row["policy"], row["width_profile"]): row
        for row in outputs.policy_width_summary
    }
    assert policy_width_rows[("TESTB", "asap", "W8_M8_F8")]["pair_count"] == 1
    assert policy_width_rows[("TESTB", "greedy_critical", "W8_M8_F4")]["pair_count"] == 1

    policy_variant_rows = {
        (row["dag_variant"], row["algorithm"], row["policy"], row["width_profile"]): row
        for row in outputs.policy_variant_summary
    }
    assert policy_variant_rows[("shifted", "TESTB", "asap", "W8_M8_F4")]["throughput_median"] == 1.1

    policy_stall_rows = {
        (row["algorithm"], row["policy"], row["raw_stall_bucket"]): row
        for row in outputs.policy_stall_summary
    }
    assert policy_stall_rows[("TESTB", "asap", "stall_high")]["pair_count"] == 2

    width_equivalence_rows = {
        (
            row["algorithm"],
            str(row["hardware_size"]),
            str(row["logical_qubits"]),
            str(row["dag_seed"]),
            row["policy"],
            str(row["issue_width"]),
            str(row["l_meas"]),
            str(row["l_ff"]),
        ): row
        for row in outputs.width_equivalence_cases
    }
    assert width_equivalence_rows[("TESTA", "4", "16", "0", "asap", "4", "1", "1")]["is_width_inactive"] == "yes"
    assert width_equivalence_rows[("TESTB", "6", "36", "0", "asap", "8", "2", "2")]["is_width_inactive"] == "no"

    stall_regression_rows = outputs.stall_regression_cases
    assert len(stall_regression_rows) == 1
    assert stall_regression_rows[0]["throughput_direction"] == "improved"

    predictor_rows = {
        (
            row["algorithm"],
            row["policy"],
            row["raw_stall_bucket"],
            row["raw_saturation_bucket"],
            row["latency_profile"],
            row["width_profile"],
        ): row
        for row in outputs.gain_predictor_summary
    }
    assert predictor_rows[("TESTA", "asap", "stall_high", "underutilized", "l1_l1", "W4_M4_F4")]["predicted_gain_band"] == "strong"

    exclusion_rows = {
        (row["scope"], row["algorithm"], str(row["hardware_size"]), str(row["logical_qubits"])): row
        for row in outputs.exclusion_summary
    }
    assert exclusion_rows[("algorithm_hq", "TESTA", "4", "16")]["missing_shifted_seed_count"] == 1
    assert exclusion_rows[("algorithm_hq", "TESTB", "6", "36")]["is_complete_pair_set"] == "yes"

    win_rows = {
        (row["dag_variant"], row["algorithm"], row["policy"], row["width_profile"]): row
        for row in outputs.policy_win_summary
    }
    assert win_rows[("shifted", "TESTB", "asap", "W8_M8_F4")]["throughput_win_count"] == 1

    vs_asap_rows = {
        (row["dag_variant"], row["algorithm"], row["policy"], row["width_profile"]): row
        for row in outputs.policy_vs_asap_summary
    }
    assert vs_asap_rows[("shifted", "TESTB", "greedy_critical", "W8_M8_F4")]["throughput_better_count_vs_asap"] == 1
    assert vs_asap_rows[("shifted", "TESTB", "greedy_critical", "W8_M8_F4")]["stall_better_count_vs_asap"] == 1


def test_analyze_shifted_study_cli(tmp_path: Path) -> None:
    sweep_csv = tmp_path / "sweep.csv"
    output_dir = tmp_path / "analysis"
    _write_sweep_csv(
        sweep_csv,
        [
            _row("raw", "TEST", 4, 16, 0, 10, 3, 1.0, 0.2, 0.5),
            _row("shifted", "TEST", 4, 16, 0, 3, 3, 1.5, 0.3, 0.75),
            _row("shifted", "TEST", 4, 16, 0, 3, 3, 1.6, 0.1, 0.8, policy="greedy_critical"),
        ],
    )

    analyze_main(["--input", str(sweep_csv), "--output-dir", str(output_dir)])

    assert (output_dir / "paired_seed_effects.csv").exists()
    assert (output_dir / "algorithm_summary.csv").exists()
    assert (output_dir / "algorithm_hq_summary.csv").exists()
    assert (output_dir / "bottleneck_summary.csv").exists()
    assert (output_dir / "policy_variant_summary.csv").exists()
    assert (output_dir / "policy_win_summary.csv").exists()
    assert (output_dir / "policy_vs_asap_summary.csv").exists()
    assert (output_dir / "policy_latency_summary.csv").exists()
    assert (output_dir / "policy_saturation_summary.csv").exists()
    assert (output_dir / "policy_width_summary.csv").exists()
    assert (output_dir / "policy_stall_summary.csv").exists()
    assert (output_dir / "width_equivalence_cases.csv").exists()
    assert (output_dir / "width_equivalence_summary.csv").exists()
    assert (output_dir / "stall_regression_cases.csv").exists()
    assert (output_dir / "stall_regression_summary.csv").exists()
    assert (output_dir / "gain_predictor_summary.csv").exists()
    assert (output_dir / "exclusion_summary.csv").exists()

    with (output_dir / "algorithm_summary.csv").open() as handle:
        row = next(csv.DictReader(handle))
    assert row["algorithm"] == "TEST"
    assert row["pair_count"] == "1"


def _write_sweep_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _row(
    dag_variant: str,
    algorithm: str,
    hardware_size: int,
    logical_qubits: int,
    dag_seed: int,
    ff_chain_depth: int,
    ff_chain_depth_shifted: int,
    throughput: float,
    stall_rate: float,
    utilization: float,
    *,
    policy: str = "asap",
    issue_width: int = 4,
    l_meas: int = 1,
    l_ff: int = 1,
    meas_width: int = 4,
    ff_width: int = 4,
) -> dict[str, object]:
    return {
        "dag_label": f"{algorithm}_H{hardware_size}_Q{logical_qubits}_s{dag_seed}_{dag_variant}",
        "dag_variant": dag_variant,
        "algorithm": algorithm,
        "hardware_size": hardware_size,
        "logical_qubits": logical_qubits,
        "dag_seed": dag_seed,
        "ff_chain_depth": ff_chain_depth,
        "ff_chain_depth_raw": ff_chain_depth if dag_variant == "raw" else 10,
        "ff_chain_depth_shifted": ff_chain_depth_shifted,
        "policy": policy,
        "release_mode": "next_cycle",
        "issue_width": issue_width,
        "l_meas": l_meas,
        "l_ff": l_ff,
        "meas_width": meas_width,
        "ff_width": ff_width,
        "total_nodes": 100,
        "total_cycles": 100,
        "throughput": throughput,
        "stall_cycles": 10,
        "stall_rate": stall_rate,
        "utilization": utilization,
    }
