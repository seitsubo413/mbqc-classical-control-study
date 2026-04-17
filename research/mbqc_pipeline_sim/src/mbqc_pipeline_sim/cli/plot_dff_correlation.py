"""CLI: visualise D_ff vs policy effectiveness (Option 3)."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot D_ff vs policy advantage over ASAP")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "results"
        / "summary"
        / "analysis"
        / "dff_policy_cases.csv",
    )
    parser.add_argument(
        "--bins",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "results"
        / "summary"
        / "analysis"
        / "dff_correlation_bins.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "results" / "figures",
    )
    args = parser.parse_args(argv)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError as exc:
        raise SystemExit(f"matplotlib/numpy required: {exc}") from exc

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ---- load data -------------------------------------------------------
    with args.cases.open() as fh:
        case_rows = list(csv.DictReader(fh))
    with args.bins.open() as fh:
        bin_rows = list(csv.DictReader(fh))

    non_asap_policies = ["greedy_critical", "shifted_critical", "stall_aware_shifted"]
    policy_colors = {
        "greedy_critical": "#2196F3",
        "shifted_critical": "#FF9800",
        "stall_aware_shifted": "#4CAF50",
    }
    policy_labels = {
        "greedy_critical": "greedy_critical",
        "shifted_critical": "shifted_critical",
        "stall_aware_shifted": "stall_aware_shifted",
    }

    # ---- Fig 1: Scatter plot (per-case), throughput vs D_ff --------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    fig.suptitle("D_ff magnitude vs policy advantage over ASAP (per case)", fontsize=13)

    for ax_idx, (dag_variant, ax) in enumerate(zip(["raw", "shifted"], axes)):
        ax.axhline(0, color="black", lw=0.8, linestyle="--", alpha=0.5)
        for policy in non_asap_policies:
            rows = [
                r for r in case_rows
                if r["dag_variant"] == dag_variant and r["policy"] == policy
            ]
            xs = [int(r["ff_chain_depth"]) for r in rows]
            ys = [float(r["throughput_vs_asap_pct"]) for r in rows]
            ax.scatter(xs, ys, alpha=0.25, s=12,
                       color=policy_colors[policy], label=policy_labels[policy])
        ax.set_xlabel("ff_chain_depth", fontsize=11)
        ax.set_ylabel("Throughput vs ASAP (%)" if ax_idx == 0 else "", fontsize=11)
        ax.set_title(f"DAG variant: {dag_variant}", fontsize=11)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_dff_throughput_scatter.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ---- Fig 2: Scatter plot (per-case), stall vs D_ff ------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    fig.suptitle("D_ff magnitude vs stall rate change vs ASAP (per case)", fontsize=13)

    for ax_idx, (dag_variant, ax) in enumerate(zip(["raw", "shifted"], axes)):
        ax.axhline(0, color="black", lw=0.8, linestyle="--", alpha=0.5)
        for policy in non_asap_policies:
            rows = [
                r for r in case_rows
                if r["dag_variant"] == dag_variant and r["policy"] == policy
            ]
            xs = [int(r["ff_chain_depth"]) for r in rows]
            ys = [float(r["stall_vs_asap_pct"]) for r in rows]
            ax.scatter(xs, ys, alpha=0.25, s=12,
                       color=policy_colors[policy], label=policy_labels[policy])
        ax.set_xlabel("ff_chain_depth", fontsize=11)
        ax.set_ylabel("Stall rate change vs ASAP (%)\n(positive = worse)" if ax_idx == 0 else "", fontsize=11)
        ax.set_title(f"DAG variant: {dag_variant}", fontsize=13)
        ax.legend(fontsize=8, loc="lower right")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_dff_stall_scatter.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ---- Fig 3: Binned summary bar chart ---------------------------------
    bin_min_order = sorted({int(r["ff_chain_depth_bin_min"]) for r in bin_rows})
    bin_labels_ordered = {
        int(r["ff_chain_depth_bin_min"]): r["ff_chain_depth_bin"] for r in bin_rows
    }

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("D_ff bin vs policy advantage over ASAP (median)", fontsize=13)

    metrics = [
        ("throughput_vs_asap_pct_median", "Throughput advantage vs ASAP (%)\n(positive = better)", "raw"),
        ("stall_vs_asap_pct_median", "Stall rate change vs ASAP (%)\n(positive = worse)", "raw"),
        ("throughput_vs_asap_pct_median", "Throughput advantage vs ASAP (%)\n(positive = better)", "shifted"),
        ("stall_vs_asap_pct_median", "Stall rate change vs ASAP (%)\n(positive = worse)", "shifted"),
    ]

    for ax, (metric, ylabel, dag_variant) in zip(axes.flat, metrics):
        ax.axhline(0, color="black", lw=0.8, linestyle="--", alpha=0.5)
        relevant_bins = sorted(
            {r["ff_chain_depth_bin"] for r in bin_rows if r["dag_variant"] == dag_variant},
            key=lambda b: int(b.split("-")[0]),
        )
        x = np.arange(len(relevant_bins))
        width = 0.25
        for i, policy in enumerate(non_asap_policies):
            vals = []
            for b in relevant_bins:
                match = [
                    r for r in bin_rows
                    if r["dag_variant"] == dag_variant
                    and r["policy"] == policy
                    and r["ff_chain_depth_bin"] == b
                ]
                vals.append(float(match[0][metric]) if match else 0.0)
            ax.bar(
                x + (i - 1) * width, vals, width,
                label=policy_labels[policy],
                color=policy_colors[policy],
                alpha=0.8,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(relevant_bins, fontsize=9)
        ax.set_xlabel("ff_chain_depth bin", fontsize=10)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(f"{dag_variant} DAG", fontsize=11)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    out = args.output_dir / "fig_dff_binned_summary.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ---- Fig 4: Combined summary (hypothesis validation) -----------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Hypothesis: D_ff magnitude determines whether complex schedulers beat ASAP",
        fontsize=12,
    )

    for ax, metric, ylabel in [
        (axes[0], "throughput_vs_asap_pct_median", "Throughput advantage vs ASAP (%)"),
        (axes[1], "stall_vs_asap_pct_median", "Stall rate change vs ASAP (%)\n(positive = worse)"),
    ]:
        ax.axhline(0, color="black", lw=1.0, linestyle="--", alpha=0.6)
        for policy in non_asap_policies:
            for dag_variant, marker, alpha in [("raw", "o", 0.9), ("shifted", "^", 0.9)]:
                rows = [
                    r for r in bin_rows
                    if r["dag_variant"] == dag_variant and r["policy"] == policy
                ]
                xs = [int(r["ff_chain_depth_bin_min"]) for r in rows]
                ys = [float(r[metric]) for r in rows]
                label = f"{policy_labels[policy]} ({dag_variant})"
                ax.plot(
                    xs, ys,
                    marker=marker,
                    linestyle="-" if dag_variant == "raw" else "--",
                    color=policy_colors[policy],
                    alpha=alpha,
                    label=label,
                    markersize=7,
                )
        ax.set_xlabel("D_ff (bin minimum)", fontsize=11)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.legend(fontsize=7, loc="best")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_dff_hypothesis_summary.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")
    print("Done.")


if __name__ == "__main__":
    main()
