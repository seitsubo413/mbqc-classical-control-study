"""CLI: Aggregate sweep results — compute median/IQR over seeds."""
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Aggregate sweep results over seeds")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "results" / "summary" / "sweep.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "results" / "summary" / "aggregated.csv",
    )
    parser.add_argument(
        "--comparison-output",
        type=Path,
        default=None,
        help="Optional CSV path for raw-vs-shifted paired comparisons",
    )
    args = parser.parse_args(argv)

    rows: list[dict[str, str]] = []
    with open(args.input) as f:
        rows = list(csv.DictReader(f))

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            f"{row['algorithm']}|H{row['hardware_size']}|Q{row['logical_qubits']}"
            f"|{row.get('dag_variant', 'raw')}"
            f"|{row['policy']}|{row.get('release_mode', 'same_cycle')}"
            f"|W{row['issue_width']}|Lm{row['l_meas']}|Lf{row['l_ff']}"
            f"|Mw{row.get('meas_width', '')}|Fw{row.get('ff_width', '')}"
        )
        grouped[key].append(row)

    out_fields = [
        "algorithm",
        "hardware_size",
        "logical_qubits",
        "dag_variant",
        "policy",
        "release_mode",
        "issue_width",
        "l_meas",
        "l_ff",
        "meas_width",
        "ff_width",
        "n_seeds",
        "total_nodes_median",
        "total_cycles_median",
        "ff_chain_depth_median",
        "throughput_median",
        "throughput_q1",
        "throughput_q3",
        "stall_rate_median",
        "stall_rate_q1",
        "stall_rate_q3",
        "utilization_median",
        "ff_chain_depth_raw_median",
        "ff_chain_depth_shifted_median",
    ]

    agg_rows: list[dict[str, str | float]] = []
    for _key, group in sorted(grouped.items()):
        rep = group[0]

        def _medians(field: str) -> tuple[float, float, float]:
            vals = sorted(float(r[field]) for r in group)
            n = len(vals)
            med = statistics.median(vals)
            q1 = statistics.median(vals[: n // 2]) if n > 1 else med
            q3 = statistics.median(vals[(n + 1) // 2 :]) if n > 1 else med
            return round(med, 6), round(q1, 6), round(q3, 6)

        tp_med, tp_q1, tp_q3 = _medians("throughput")
        sr_med, sr_q1, sr_q3 = _medians("stall_rate")
        ut_med, _, _ = _medians("utilization")
        tc_med, _, _ = _medians("total_cycles")
        tn_med, _, _ = _medians("total_nodes")
        fd_sel_med, _, _ = _medians("ff_chain_depth")
        fd_med, _, _ = _medians("ff_chain_depth_raw")
        shifted_depth_values = [float(r["ff_chain_depth_shifted"]) for r in group if r.get("ff_chain_depth_shifted", "")]
        fd_shifted_med = round(statistics.median(sorted(shifted_depth_values)), 6) if shifted_depth_values else ""

        agg_rows.append(
            {
                "algorithm": rep["algorithm"],
                "hardware_size": rep["hardware_size"],
                "logical_qubits": rep["logical_qubits"],
                "dag_variant": rep.get("dag_variant", "raw"),
                "policy": rep["policy"],
                "release_mode": rep.get("release_mode", "same_cycle"),
                "issue_width": rep["issue_width"],
                "l_meas": rep["l_meas"],
                "l_ff": rep["l_ff"],
                "meas_width": rep.get("meas_width", ""),
                "ff_width": rep.get("ff_width", ""),
                "n_seeds": len(group),
                "total_nodes_median": tn_med,
                "total_cycles_median": tc_med,
                "ff_chain_depth_median": fd_sel_med,
                "throughput_median": tp_med,
                "throughput_q1": tp_q1,
                "throughput_q3": tp_q3,
                "stall_rate_median": sr_med,
                "stall_rate_q1": sr_q1,
                "stall_rate_q3": sr_q3,
                "utilization_median": ut_med,
                "ff_chain_depth_raw_median": fd_med,
                "ff_chain_depth_shifted_median": fd_shifted_med,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(agg_rows)

    print(f"Aggregated {len(rows)} rows → {len(agg_rows)} groups → {args.output}")
    if args.comparison_output is not None:
        comparison_rows = _build_variant_comparison_rows(agg_rows)
        args.comparison_output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.comparison_output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_comparison_fieldnames())
            writer.writeheader()
            writer.writerows(comparison_rows)
        print(f"Paired raw/shifted groups → {len(comparison_rows)} rows → {args.comparison_output}")


def _build_variant_comparison_rows(
    agg_rows: list[dict[str, str | float]],
) -> list[dict[str, str | float]]:
    grouped: dict[str, dict[str, dict[str, str | float]]] = defaultdict(dict)
    for row in agg_rows:
        dag_variant = str(row["dag_variant"])
        key = (
            f"{row['algorithm']}|H{row['hardware_size']}|Q{row['logical_qubits']}"
            f"|{row['policy']}|{row['release_mode']}"
            f"|W{row['issue_width']}|Lm{row['l_meas']}|Lf{row['l_ff']}"
            f"|Mw{row['meas_width']}|Fw{row['ff_width']}"
        )
        grouped[key][dag_variant] = row

    comparison_rows: list[dict[str, str | float]] = []
    for key in sorted(grouped):
        variants = grouped[key]
        if "raw" not in variants or "shifted" not in variants:
            continue
        raw_row = variants["raw"]
        shifted_row = variants["shifted"]
        raw_depth = float(raw_row["ff_chain_depth_median"])
        shifted_depth = float(shifted_row["ff_chain_depth_median"])
        raw_throughput = float(raw_row["throughput_median"])
        shifted_throughput = float(shifted_row["throughput_median"])
        raw_stall = float(raw_row["stall_rate_median"])
        shifted_stall = float(shifted_row["stall_rate_median"])
        raw_util = float(raw_row["utilization_median"])
        shifted_util = float(shifted_row["utilization_median"])
        comparison_rows.append(
            {
                "algorithm": raw_row["algorithm"],
                "hardware_size": raw_row["hardware_size"],
                "logical_qubits": raw_row["logical_qubits"],
                "policy": raw_row["policy"],
                "release_mode": raw_row["release_mode"],
                "issue_width": raw_row["issue_width"],
                "l_meas": raw_row["l_meas"],
                "l_ff": raw_row["l_ff"],
                "meas_width": raw_row["meas_width"],
                "ff_width": raw_row["ff_width"],
                "n_seeds_raw": raw_row["n_seeds"],
                "n_seeds_shifted": shifted_row["n_seeds"],
                "ff_chain_depth_raw_median": raw_depth,
                "ff_chain_depth_shifted_median": shifted_depth,
                "depth_reduction_pct": _pct_reduction(raw_depth, shifted_depth),
                "throughput_raw_median": raw_throughput,
                "throughput_shifted_median": shifted_throughput,
                "throughput_delta": round(shifted_throughput - raw_throughput, 6),
                "throughput_gain_pct": _pct_change(raw_throughput, shifted_throughput),
                "stall_rate_raw_median": raw_stall,
                "stall_rate_shifted_median": shifted_stall,
                "stall_rate_delta": round(shifted_stall - raw_stall, 6),
                "stall_reduction_pct": _pct_reduction(raw_stall, shifted_stall),
                "utilization_raw_median": raw_util,
                "utilization_shifted_median": shifted_util,
                "utilization_delta": round(shifted_util - raw_util, 6),
                "utilization_gain_pct": _pct_change(raw_util, shifted_util),
            }
        )
    return comparison_rows


def _comparison_fieldnames() -> list[str]:
    return [
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


def _pct_change(base: float, new: float) -> float:
    if base == 0.0:
        return 0.0 if new == 0.0 else 100.0
    return round(((new - base) / base) * 100.0, 6)


def _pct_reduction(base: float, reduced: float) -> float:
    if base == 0.0:
        return 0.0 if reduced == 0.0 else -100.0
    return round(((base - reduced) / base) * 100.0, 6)


if __name__ == "__main__":
    main()
