"""CLI: Visualise ff_width sweep — design boundary (Option 2)."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot ff_width sweep results")
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
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

    with (args.analysis_dir / "policy_width_summary.csv").open() as fh:
        rows = list(csv.DictReader(fh))

    ff_widths = [4, 5, 6, 7, 8]
    algorithms = ["QAOA", "QFT", "VQE"]
    policies = ["asap", "greedy_critical", "stall_aware_shifted"]

    alg_colors = {"QAOA": "#1565C0", "QFT": "#C62828", "VQE": "#2E7D32"}
    policy_ls = {"asap": "-", "greedy_critical": "--", "stall_aware_shifted": ":"}
    policy_marker = {"asap": "o", "greedy_critical": "s", "stall_aware_shifted": "^"}

    def _get(alg: str, policy: str, ff_w: int, metric: str) -> float | None:
        for r in rows:
            if (r["algorithm"] == alg
                    and r["policy"] == policy
                    and r["width_profile"] == f"W8_M8_F{ff_w}"):
                return float(r[metric])
        return None

    # ── Fig 1: Stall reduction (raw→shifted) vs ff_width per algorithm ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=False)
    fig.suptitle(
        "Stall reduction (%) when using shifted DAG vs ff_width\n"
        "Positive = stall improved, Negative = stall regression (worse)",
        fontsize=12,
    )
    for ax, alg in zip(axes, algorithms):
        ax.axhline(0, color="black", lw=1.2, linestyle="--", alpha=0.7, label="breakeven")
        for policy in policies:
            ys = [_get(alg, policy, fw, "stall_reduction_pct_median") for fw in ff_widths]
            ys_clean = [y if y is not None else float("nan") for y in ys]
            ax.plot(
                ff_widths, ys_clean,
                color=alg_colors[alg],
                ls=policy_ls[policy],
                marker=policy_marker[policy],
                markersize=7,
                label=policy,
                alpha=0.9,
            )
            # Mark crossover point
            for i in range(len(ys_clean) - 1):
                if (not np.isnan(ys_clean[i]) and not np.isnan(ys_clean[i + 1])
                        and ys_clean[i] < 0 <= ys_clean[i + 1]):
                    ax.axvline(ff_widths[i] + 0.5, color="gray", lw=0.8, ls=":", alpha=0.6)
                    ax.annotate(
                        f"F*≈{ff_widths[i]+0.5:.0f}",
                        xy=(ff_widths[i] + 0.5, 0),
                        xytext=(ff_widths[i] + 0.5 + 0.1, 30),
                        fontsize=8, color="gray",
                    )
        ax.set_title(alg, fontsize=12, color=alg_colors[alg])
        ax.set_xlabel("ff_width", fontsize=11)
        ax.set_ylabel("Stall reduction % (raw→shifted)" if alg == "QAOA" else "", fontsize=10)
        ax.set_xticks(ff_widths)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_ffwidth_stall_reduction.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 2: Throughput gain (raw→shifted) vs ff_width ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=False)
    fig.suptitle(
        "Throughput gain (%) when using shifted DAG vs ff_width\n"
        "(positive = shifted is better, always positive here)",
        fontsize=12,
    )
    for ax, alg in zip(axes, algorithms):
        ax.axhline(0, color="black", lw=0.8, linestyle="--", alpha=0.5)
        for policy in policies:
            ys = [_get(alg, policy, fw, "throughput_gain_pct_median") for fw in ff_widths]
            ys_clean = [y if y is not None else float("nan") for y in ys]
            ax.plot(
                ff_widths, ys_clean,
                color=alg_colors[alg],
                ls=policy_ls[policy],
                marker=policy_marker[policy],
                markersize=7,
                label=policy,
                alpha=0.9,
            )
        ax.set_title(alg, fontsize=12, color=alg_colors[alg])
        ax.set_xlabel("ff_width", fontsize=11)
        ax.set_ylabel("Throughput gain % (raw→shifted)" if alg == "QAOA" else "", fontsize=10)
        ax.set_xticks(ff_widths)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_ffwidth_throughput_gain.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 3: Combined — stall + throughput in one panel per algorithm ──
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(
        "ff_width sweep: shifted DAG benefit vs hardware provisioning\n"
        "(W=8, M=8, L_meas=1, L_ff=2)",
        fontsize=13,
    )
    for col, alg in enumerate(algorithms):
        for row, (metric, ylabel, add_hline) in enumerate([
            ("throughput_gain_pct_median", "Throughput gain % (raw→shifted)", False),
            ("stall_reduction_pct_median", "Stall reduction % (positive = better)", True),
        ]):
            ax = axes[row][col]
            if add_hline:
                ax.axhline(0, color="black", lw=1.2, linestyle="--", alpha=0.7)
            for policy in policies:
                ys = [_get(alg, policy, fw, metric) for fw in ff_widths]
                ys_clean = [y if y is not None else float("nan") for y in ys]
                ax.plot(
                    ff_widths, ys_clean,
                    color=alg_colors[alg],
                    ls=policy_ls[policy],
                    marker=policy_marker[policy],
                    markersize=7,
                    label=policy,
                    alpha=0.9,
                )
            if col == 0:
                ax.set_ylabel(ylabel, fontsize=10)
            if row == 0:
                ax.set_title(alg, fontsize=12, color=alg_colors[alg])
            ax.set_xlabel("ff_width" if row == 1 else "", fontsize=10)
            ax.set_xticks(ff_widths)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_ffwidth_combined.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Print design boundary table ──
    print("\n=== Stall regression crossover (F* = minimum ff_width for stall improvement) ===")
    print(f"{'Algorithm':<10} {'Policy':<25} {'F*':<8} {'Stall at F4':<14} {'Stall at F8'}")
    for alg in algorithms:
        for policy in policies:
            stall_vals = [_get(alg, policy, fw, "stall_reduction_pct_median") for fw in ff_widths]
            f_star = None
            for i, fw in enumerate(ff_widths):
                v = stall_vals[i]
                if v is not None and v >= 0:
                    f_star = fw
                    break
            s4 = stall_vals[0]
            s8 = stall_vals[-1]
            print(
                f"  {alg:<8} {policy:<25} "
                f"F*={f_star if f_star else '>8':<4}  "
                f"F4={s4:>8.1f}%  F8={s8:>8.1f}%"
            )

    print("Done.")


if __name__ == "__main__":
    main()
