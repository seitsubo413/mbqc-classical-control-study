"""CLI: Visualise ready-burst patterns raw vs shifted (Option 1)."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot ready-burst cycle records")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "results"
        / "studies"
        / "burst_analysis"
        / "cycle_records.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "results"
        / "studies"
        / "burst_analysis"
        / "figures",
    )
    args = parser.parse_args(argv)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:
        raise SystemExit(f"matplotlib/numpy required: {exc}") from exc

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with args.input.open() as fh:
        rows = list(csv.DictReader(fh))

    def _rows(alg: str, h: int, q: int, policy: str, variant: str) -> list[dict]:
        return [
            r for r in rows
            if r["algorithm"] == alg
            and int(r["hardware_size"]) == h
            and int(r["logical_qubits"]) == q
            and r["policy"] == policy
            and r["dag_variant"] == variant
        ]

    # Cases: (alg, H, Q, label, D_ff_raw, D_ff_shifted)
    cases = [
        ("QAOA", 8, 64, "QAOA H8/Q64", 142, 2),
        ("QFT",  6, 36, "QFT H6/Q36",  177, 10),
        ("QFT",  4, 16, "QFT H4/Q16",  77,  7),
        ("VQE",  8, 64, "VQE H8/Q64",  63,  1),
    ]

    variant_colors = {"raw": "#1565C0", "shifted": "#C62828"}
    variant_ls     = {"raw": "-",       "shifted": "--"}

    # ── Fig 1: ready_queue_size time series (ASAP only, normalised by total_nodes) ──
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        "Ready queue size over time: raw vs shifted (ASAP, W8 M8 F4 L_meas=1 L_ff=2)",
        fontsize=12,
    )
    for ax, (alg, h, q, label, d_raw, d_shifted) in zip(axes.flat, cases):
        for variant in ["raw", "shifted"]:
            r = _rows(alg, h, q, "asap", variant)
            if not r:
                continue
            cycles = [int(x["cycle"]) for x in r]
            rqs = [int(x["ready_queue_size"]) for x in r]
            total_nodes = int(r[0]["total_nodes"])
            ax.plot(
                cycles,
                [v / total_nodes * 100 for v in rqs],
                color=variant_colors[variant],
                lw=0.8,
                ls=variant_ls[variant],
                alpha=0.85,
                label=f"{variant} (D_ff={d_raw if variant == 'raw' else d_shifted})",
            )
        ax.set_title(f"{label}", fontsize=11)
        ax.set_xlabel("Cycle", fontsize=10)
        ax.set_ylabel("Ready queue (% of total nodes)", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = args.output_dir / "fig_burst_timeseries_asap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 2: ready_queue_size histogram raw vs shifted, ASAP ──
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Ready queue size distribution: raw vs shifted (ASAP)", fontsize=12)
    for ax, (alg, h, q, label, d_raw, d_shifted) in zip(axes.flat, cases):
        bins = np.linspace(0, 30, 31)
        for variant in ["raw", "shifted"]:
            r = _rows(alg, h, q, "asap", variant)
            if not r:
                continue
            rqs = [int(x["ready_queue_size"]) for x in r]
            ax.hist(
                rqs,
                bins=bins,
                color=variant_colors[variant],
                alpha=0.55,
                label=f"{variant} (D_ff={d_raw if variant == 'raw' else d_shifted})",
                density=True,
            )
        ax.set_title(f"{label}", fontsize=11)
        ax.set_xlabel("ready_queue_size (nodes)", fontsize=10)
        ax.set_ylabel("Density", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = args.output_dir / "fig_burst_histogram_asap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 3: ff_waiting_queue raw vs shifted (burst downstream effect) ──
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        "FF waiting queue size over time: raw vs shifted (ASAP)\n"
        "(positive spikes = burst overflowing FF capacity)",
        fontsize=12,
    )
    for ax, (alg, h, q, label, d_raw, d_shifted) in zip(axes.flat, cases):
        for variant in ["raw", "shifted"]:
            r = _rows(alg, h, q, "asap", variant)
            if not r:
                continue
            cycles = [int(x["cycle"]) for x in r]
            wff = [int(x["waiting_ff_queue_size"]) for x in r]
            max_wff = max(wff) if wff else 0
            ax.plot(
                cycles, wff,
                color=variant_colors[variant],
                lw=0.8,
                ls=variant_ls[variant],
                alpha=0.85,
                label=f"{variant} (D_ff={d_raw if variant == 'raw' else d_shifted}, max={max_wff})",
            )
        ax.set_title(f"{label}", fontsize=11)
        ax.set_xlabel("Cycle", fontsize=10)
        ax.set_ylabel("FF waiting queue size", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = args.output_dir / "fig_burst_ff_waiting_asap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 4: ASAP vs greedy_critical, shifted DAG only ──
    policy_colors = {"asap": "#1B5E20", "greedy_critical": "#E65100"}
    policy_ls     = {"asap": "-",       "greedy_critical": "--"}

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        "FF waiting queue: ASAP vs greedy_critical on shifted DAG\n"
        "(shows why complex policy worsens stall on shifted)",
        fontsize=12,
    )
    for ax, (alg, h, q, label, d_raw, d_shifted) in zip(axes.flat, cases):
        for policy in ["asap", "greedy_critical"]:
            r = _rows(alg, h, q, policy, "shifted")
            if not r:
                continue
            cycles = [int(x["cycle"]) for x in r]
            wff = [int(x["waiting_ff_queue_size"]) for x in r]
            stall_cyc = sum(1 for x in r if int(x["issued"]) == 0)
            total_cyc = len(r)
            stall_pct = stall_cyc / total_cyc * 100
            ax.plot(
                cycles, wff,
                color=policy_colors[policy],
                lw=0.8,
                ls=policy_ls[policy],
                alpha=0.85,
                label=f"{policy} (stall={stall_pct:.1f}%)",
            )
        ax.set_title(f"{label} — shifted (D_ff={d_shifted})", fontsize=11)
        ax.set_xlabel("Cycle", fontsize=10)
        ax.set_ylabel("FF waiting queue size", fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = args.output_dir / "fig_burst_policy_shifted.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 5: Summary statistics table plot ──
    summary = []
    for alg, h, q, label, d_raw, d_shifted in cases:
        for variant in ["raw", "shifted"]:
            for policy in _POLICIES:
                r = _rows(alg, h, q, policy, variant)
                if not r:
                    continue
                rqs = [int(x["ready_queue_size"]) for x in r]
                wff = [int(x["waiting_ff_queue_size"]) for x in r]
                stall_cyc = sum(1 for x in r if int(x["issued"]) == 0)
                summary.append({
                    "case": label,
                    "variant": variant,
                    "policy": policy,
                    "d_ff": d_raw if variant == "raw" else d_shifted,
                    "ready_mean": np.mean(rqs),
                    "ready_max": max(rqs),
                    "ready_p99": np.percentile(rqs, 99),
                    "wff_mean": np.mean(wff),
                    "wff_max": max(wff),
                    "stall_pct": stall_cyc / len(r) * 100,
                })

    # Save summary CSV
    out_csv = args.output_dir.parent / "burst_summary.csv"
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    print(f"Saved summary: {out_csv}")

    print("Done.")


_POLICIES = ["asap", "greedy_critical"]


if __name__ == "__main__":
    main()
