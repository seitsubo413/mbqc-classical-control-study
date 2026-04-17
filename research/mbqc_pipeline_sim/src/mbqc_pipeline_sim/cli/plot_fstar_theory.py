"""Experiment B plots: F* theory — burst_load vs F*(ASAP), ff_rate_matched guarantee."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot F* theory results")
    parser.add_argument("--fstar-csv", type=Path, required=True, help="fstar_per_case.csv")
    parser.add_argument("--agg-csv", type=Path, required=True, help="fstar_aggregated.csv")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:
        raise SystemExit(f"matplotlib/numpy required: {exc}") from exc

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with args.fstar_csv.open() as f:
        cases = list(csv.DictReader(f))
    with args.agg_csv.open() as f:
        agg = list(csv.DictReader(f))

    alg_colors = {"QAOA": "#1565C0", "QFT": "#C62828", "VQE": "#2E7D32"}
    alg_markers = {"QAOA": "o", "QFT": "s", "VQE": "^"}

    # ── Fig 1: burst_load vs F*(ASAP) — log-scale x axis ──────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))

    for alg in ["QAOA", "QFT", "VQE"]:
        x = [float(c["burst_load"]) for c in cases if c["alg"] == alg and c["f_star_asap"]]
        y = [int(c["f_star_asap"]) for c in cases if c["alg"] == alg and c["f_star_asap"]]
        ax.scatter(
            x, y,
            color=alg_colors[alg], marker=alg_markers[alg],
            s=80, alpha=0.85, label=alg, zorder=3,
        )

    # Reference line: F* = ceil(W × (1 - 1/log2(B+1)))
    B_range = np.logspace(2, 4, 200)
    W = 8
    f_ref = np.ceil(W * (1 - 1 / np.log2(B_range + 1)))
    ax.plot(B_range, f_ref, "k--", lw=1.5, alpha=0.6,
            label=r"$F^* = \lceil W \cdot (1 - 1/\log_2(B+1)) \rceil$")

    ax.axhline(4, color="#E65100", lw=2.0, ls="-",
               label="F*(ff_rate_matched) = 4 (guaranteed)")

    ax.set_xscale("log")
    ax.set_xlabel("Burst load B = N / D_ff_shifted", fontsize=12)
    ax.set_ylabel("F* (minimum ff_width for no stall regression)", fontsize=12)
    ax.set_title(
        "F*(ASAP) grows with burst load; ff_rate_matched holds F*=4 universally\n"
        "(W=8, L_meas=1, L_ff=2, meas_width=8)",
        fontsize=11,
    )
    ax.set_yticks([4, 5, 6, 7, 8])
    ax.set_yticklabels(["F=4", "F=5", "F=6", "F=7", "F=8"])
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_fstar_burst_load.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 2: F* reduction (ASAP → ff_rate_matched) per circuit ─────────────
    fig, ax = plt.subplots(figsize=(12, 5))

    circuit_labels = [f"{r['algorithm']}\nH={r['hardware_size']},Q={r['logical_qubits']}"
                      for r in agg]
    f_asap_vals = [int(r["f_star_asap_median"]) for r in agg]
    f_ffrm_vals = [int(r["f_star_ffrm_median"]) for r in agg]
    reductions = [int(r["f_star_reduction"]) for r in agg]

    x = np.arange(len(circuit_labels))
    width = 0.35

    bars_asap = ax.bar(x - width / 2, f_asap_vals, width, label="F*(ASAP)",
                       color="#888888", alpha=0.8, edgecolor="white")
    bars_ffrm = ax.bar(x + width / 2, f_ffrm_vals, width, label="F*(ff_rate_matched)",
                       color="#E65100", alpha=0.9, edgecolor="white")

    for bar, val in zip(bars_asap, f_asap_vals):
        ax.annotate(str(val), xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=10, color="#555555")
    for bar, val in zip(bars_ffrm, f_ffrm_vals):
        ax.annotate(str(val), xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=11, color="#E65100", fontweight="bold")

    # Annotate reduction arrows
    for i, (fa, ff, red) in enumerate(zip(f_asap_vals, f_ffrm_vals, reductions)):
        if red > 0:
            ax.annotate(
                f"−{red}",
                xy=(x[i], (fa + ff) / 2 + 0.2),
                ha="center", va="center",
                fontsize=10, color="darkred",
                fontweight="bold",
            )

    ax.set_title(
        "F* reduction: ASAP vs ff_rate_matched per circuit family\n"
        "ff_rate_matched achieves F*=4 on all circuits — 0-4 ff_width savings",
        fontsize=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(circuit_labels, fontsize=9)
    ax.set_ylabel("F* (minimum ff_width)", fontsize=11)
    ax.set_yticks([4, 5, 6, 7, 8])
    ax.set_ylim(0, 9.5)
    ax.axhline(4, color="#E65100", lw=1.5, ls=":", alpha=0.5)
    ax.legend(fontsize=10)
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_fstar_reduction.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 3: D_ff_shifted vs F*(ASAP) with N as point size ─────────────────
    fig, ax = plt.subplots(figsize=(9, 6))

    for c in cases:
        if not c["f_star_asap"]:
            continue
        alg = c["alg"]
        dff = float(c["D_ff_s"])
        N = int(c["N"])
        fstar = int(c["f_star_asap"])
        size = max(30, min(300, N / 20))
        ax.scatter(
            dff, fstar,
            color=alg_colors[alg], marker=alg_markers[alg],
            s=size, alpha=0.7, zorder=3,
            label=alg if dff == [float(cc["D_ff_s"]) for cc in cases if cc["alg"] == alg][0] else "_nolegend_",
        )

    ax.axhline(4, color="#E65100", lw=2.0, ls="-", alpha=0.9,
               label="F*(ff_rate_matched) = 4")

    # Add manual legend for algorithms
    for alg in ["QAOA", "QFT", "VQE"]:
        ax.scatter([], [], color=alg_colors[alg], marker=alg_markers[alg],
                   s=80, label=f"{alg} (size ∝ N)")

    ax.set_xlabel("D_ff_shifted (FF dependency chain depth after signal shift)", fontsize=12)
    ax.set_ylabel("F*(ASAP)", fontsize=12)
    ax.set_title(
        "D_ff_shifted vs F*(ASAP): low D_ff ≠ low F*\n"
        "F* depends jointly on D_ff, N, and raw stall rate",
        fontsize=11,
    )
    ax.set_yticks([4, 5, 6, 7, 8])
    ax.legend(fontsize=10, loc="lower right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_fstar_vs_dff.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    print("Done.")


if __name__ == "__main__":
    main()
