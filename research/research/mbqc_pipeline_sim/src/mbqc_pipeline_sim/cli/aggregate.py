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
    args = parser.parse_args(argv)

    rows: list[dict[str, str]] = []
    with open(args.input) as f:
        rows = list(csv.DictReader(f))

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            f"{row['algorithm']}|H{row['hardware_size']}|Q{row['logical_qubits']}"
            f"|{row['policy']}|{row.get('release_mode', 'same_cycle')}"
            f"|W{row['issue_width']}|Lm{row['l_meas']}|Lf{row['l_ff']}"
            f"|Mw{row.get('meas_width', '')}|Fw{row.get('ff_width', '')}"
        )
        grouped[key].append(row)

    out_fields = [
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
        "n_seeds",
        "total_nodes_median",
        "total_cycles_median",
        "throughput_median",
        "throughput_q1",
        "throughput_q3",
        "stall_rate_median",
        "stall_rate_q1",
        "stall_rate_q3",
        "utilization_median",
        "ff_chain_depth_raw_median",
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
        fd_med, _, _ = _medians("ff_chain_depth_raw")

        agg_rows.append(
            {
                "algorithm": rep["algorithm"],
                "hardware_size": rep["hardware_size"],
                "logical_qubits": rep["logical_qubits"],
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
                "throughput_median": tp_med,
                "throughput_q1": tp_q1,
                "throughput_q3": tp_q3,
                "stall_rate_median": sr_med,
                "stall_rate_q1": sr_q1,
                "stall_rate_q3": sr_q3,
                "utilization_median": ut_med,
                "ff_chain_depth_raw_median": fd_med,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(agg_rows)

    print(f"Aggregated {len(rows)} rows → {len(agg_rows)} groups → {args.output}")


if __name__ == "__main__":
    main()
