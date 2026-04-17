#!/usr/bin/env python3
"""Study 20: ASAP vs ff_rate_matched for large-scale circuits (H=10/12).

Key question: Does F*(ff_rate_matched) = 4 hold for H>=10?
             How does F*(ASAP) behave as burst_load grows?
"""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    sweep_path = here / "summary" / "sweep.csv"
    out_dir = here / "summary"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Load and pair ASAP vs ff_rate_matched ────────────────────────────────
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
            rows_by_key[key][row["policy"]] = row

    fieldnames = [
        "algorithm", "hardware_size", "logical_qubits", "dag_seed", "dag_label",
        "issue_width", "meas_width", "ff_width", "l_meas", "l_ff", "f_over_w",
        "total_cycles_asap", "total_cycles_ff_rate_matched", "cycles_ratio_ff_over_asap",
        "throughput_asap", "throughput_ff_rate_matched", "throughput_gain_pct",
        "stall_rate_asap", "stall_rate_ff_rate_matched", "stall_rate_delta",
    ]
    out_rows: list[dict] = []
    missing = 0
    for key, polmap in sorted(rows_by_key.items()):
        if "asap" not in polmap or "ff_rate_matched" not in polmap:
            missing += 1
            continue
        a, b = polmap["asap"], polmap["ff_rate_matched"]
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
        out_rows.append({
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
        })

    paired_path = out_dir / "paired_comparison.csv"
    with paired_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {len(out_rows)} rows → {paired_path}")
    if missing:
        print(f"Skipped {missing} incomplete keys")

    _write_summary(out_dir, out_rows)


def _write_summary(out_dir: Path, rows: list[dict]) -> None:
    def med(vals: list[float]) -> float:
        return float(statistics.median(vals)) if vals else float("nan")

    cycles_ratios = [float(r["cycles_ratio_ff_over_asap"]) for r in rows]
    tp_gains = [float(r["throughput_gain_pct"]) for r in rows]
    eq = sum(1 for x in cycles_ratios if abs(x - 1.0) < 1e-9)
    gt = sum(1 for x in cycles_ratios if x > 1.0 + 1e-9)
    lt = sum(1 for x in cycles_ratios if x < 1.0 - 1e-9)

    lines = [
        "Study 20: ASAP vs ff_rate_matched — Large-scale H=10/12",
        f"Paired rows: {len(rows)}",
        "",
        "Global:",
        f"  median(cycles_ratio_ff_over_asap) = {med(cycles_ratios):.6f}  (1.0 = same total_cycles)",
        f"  median(throughput_gain_pct) = {med(tp_gains):.4f}%",
        f"  cycles_ratio == 1.0: {eq}",
        f"  cycles_ratio >  1.0: {gt}  (ff_rate_matched slower)",
        f"  cycles_ratio <  1.0: {lt}  (ff_rate_matched faster)",
        "",
        "By F/W and issue_width (median cycles_ratio):",
    ]
    bucket: dict[tuple, list[float]] = defaultdict(list)
    for r in rows:
        bucket[(float(r["f_over_w"]), int(r["issue_width"]))].append(
            float(r["cycles_ratio_ff_over_asap"])
        )
    for (fw, w) in sorted(bucket.keys()):
        v = bucket[(fw, w)]
        lines.append(f"  F/W={fw:.4f}  issue_width={w:2d}  n={len(v):3d}  median_cycles_ratio={med(v):.6f}")

    # ── Stall rate by algorithm × hq_pair × policy × ff_width ────────────────
    lines += ["", "Stall rate by (algorithm, H, Q, ff_width):"]
    stall_bucket: dict[tuple, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        k = (r["algorithm"], r["hardware_size"], r["logical_qubits"], r["ff_width"])
        stall_bucket[k]["asap"].append(float(r["stall_rate_asap"]))
        stall_bucket[k]["ff_rm"].append(float(r["stall_rate_ff_rate_matched"]))

    for k in sorted(stall_bucket.keys()):
        alg, H, Q, fw = k
        s_a = med(stall_bucket[k]["asap"])
        s_f = med(stall_bucket[k]["ff_rm"])
        lines.append(
            f"  {alg} H={H} Q={Q:>3} ff_width={fw}  "
            f"asap={s_a:.4f}  ff_rate_matched={s_f:.4f}"
        )

    # ── Throughput cost by algorithm × hq_pair (issue_width=8, ff_width=4) ──
    lines += ["", "Throughput cost (issue_width=8, ff_width=4) — representative:"]
    rep_rows = [
        r for r in rows
        if int(r["issue_width"]) == 8 and int(r["ff_width"]) == 4
    ]
    rep_bucket: dict[tuple, list[float]] = defaultdict(list)
    for r in rep_rows:
        rep_bucket[(r["algorithm"], r["hardware_size"], r["logical_qubits"])].append(
            float(r["cycles_ratio_ff_over_asap"])
        )
    for k in sorted(rep_bucket.keys()):
        alg, H, Q = k
        v = rep_bucket[k]
        lines.append(
            f"  {alg} H={H} Q={Q:>3}  median_cycles_ratio={med(v):.6f}  n={len(v)}"
        )

    summary_path = out_dir / "study20_summary.txt"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote summary → {summary_path}")


if __name__ == "__main__":
    main()
