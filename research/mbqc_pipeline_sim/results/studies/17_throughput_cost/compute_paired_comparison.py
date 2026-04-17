#!/usr/bin/env python3
"""Pair ASAP vs ff_rate_matched rows from study 17 sweep.csv (stdlib only)."""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    sweep_path = here / "summary" / "sweep.csv"
    out_path = here / "summary" / "paired_comparison.csv"

    rows_by_key: dict[tuple, dict[str, dict]] = defaultdict(dict)
    with sweep_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (
                row["dag_label"],
                row["issue_width"],
                row["meas_width"],
                row["ff_width"],
                row["l_meas"],
                row["l_ff"],
                row["release_mode"],
            )
            pol = row["policy"]
            rows_by_key[key][pol] = row

    fieldnames = [
        "algorithm",
        "hardware_size",
        "logical_qubits",
        "dag_seed",
        "dag_label",
        "issue_width",
        "meas_width",
        "ff_width",
        "l_meas",
        "l_ff",
        "f_over_w",
        "total_cycles_asap",
        "total_cycles_ff_rate_matched",
        "cycles_ratio_ff_over_asap",
        "throughput_asap",
        "throughput_ff_rate_matched",
        "throughput_gain_pct",
        "stall_rate_asap",
        "stall_rate_ff_rate_matched",
        "stall_rate_delta",
    ]
    out_rows: list[dict[str, str]] = []
    missing = 0
    for key, polmap in sorted(rows_by_key.items(), key=lambda x: x[0]):
        if "asap" not in polmap or "ff_rate_matched" not in polmap:
            missing += 1
            continue
        a = polmap["asap"]
        b = polmap["ff_rate_matched"]
        issue_w = int(a["issue_width"])
        ff_w = int(a["ff_width"])
        f_over_w = ff_w / issue_w if issue_w else float("nan")

        c_asap = int(a["total_cycles"])
        c_ff = int(b["total_cycles"])
        cycles_ratio = c_ff / c_asap if c_asap else float("nan")

        t_asap = float(a["throughput"])
        t_ff = float(b["throughput"])
        tp_gain_pct = (t_ff - t_asap) / t_asap * 100.0 if t_asap else float("nan")

        s_asap = float(a["stall_rate"])
        s_ff = float(b["stall_rate"])

        out_rows.append(
            {
                "algorithm": a["algorithm"],
                "hardware_size": a["hardware_size"],
                "logical_qubits": a["logical_qubits"],
                "dag_seed": a["dag_seed"],
                "dag_label": a["dag_label"],
                "issue_width": a["issue_width"],
                "meas_width": a["meas_width"],
                "ff_width": a["ff_width"],
                "l_meas": a["l_meas"],
                "l_ff": a["l_ff"],
                "f_over_w": f"{f_over_w:.6f}",
                "total_cycles_asap": str(c_asap),
                "total_cycles_ff_rate_matched": str(c_ff),
                "cycles_ratio_ff_over_asap": f"{cycles_ratio:.6f}",
                "throughput_asap": a["throughput"],
                "throughput_ff_rate_matched": b["throughput"],
                "throughput_gain_pct": f"{tp_gain_pct:.6f}",
                "stall_rate_asap": a["stall_rate"],
                "stall_rate_ff_rate_matched": b["stall_rate"],
                "stall_rate_delta": f"{s_ff - s_asap:.6f}",
            }
        )

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows → {out_path}")
    if missing:
        print(f"Skipped {missing} incomplete keys (missing asap or ff_rate_matched)")

    _write_summary(out_path, out_rows)


def _write_summary(paired_csv: Path, rows: list[dict[str, str]]) -> None:
    summary_path = paired_csv.parent / "study17_summary.txt"
    cycles_ratios = [float(r["cycles_ratio_ff_over_asap"]) for r in rows]
    tp_gains = [float(r["throughput_gain_pct"]) for r in rows]
    eq_cycles = sum(1 for x in cycles_ratios if abs(x - 1.0) < 1e-9)
    gt_cycles = sum(1 for x in cycles_ratios if x > 1.0 + 1e-9)
    lt_cycles = sum(1 for x in cycles_ratios if x < 1.0 - 1e-9)

    def med(vals: list[float]) -> float:
        return float(statistics.median(vals)) if vals else float("nan")

    lines = [
        "Study 17: ASAP vs ff_rate_matched (shifted DAG)",
        f"Paired rows: {len(rows)}",
        "",
        "Global:",
        f"  median(cycles_ratio_ff_over_asap) = {med(cycles_ratios):.6f}  (1.0 = same total_cycles)",
        f"  median(throughput_gain_pct) = {med(tp_gains):.4f}%",
        f"  cycles_ratio == 1.0: {eq_cycles}",
        f"  cycles_ratio >  1.0: {gt_cycles}  (ff_rate_matched slower)",
        f"  cycles_ratio <  1.0: {lt_cycles}  (ff_rate_matched faster)",
        "",
        "By F/W and issue_width (median cycles_ratio):",
    ]

    bucket: dict[tuple[float, int], list[float]] = defaultdict(list)
    for r in rows:
        bucket[(float(r["f_over_w"]), int(r["issue_width"]))].append(
            float(r["cycles_ratio_ff_over_asap"])
        )
    for (f_w, w) in sorted(bucket.keys()):
        v = bucket[(f_w, w)]
        lines.append(
            f"  F/W={f_w:.4f}  issue_width={w:2d}  n={len(v):3d}  median_cycles_ratio={med(v):.6f}"
        )

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote summary → {summary_path}")


if __name__ == "__main__":
    main()
