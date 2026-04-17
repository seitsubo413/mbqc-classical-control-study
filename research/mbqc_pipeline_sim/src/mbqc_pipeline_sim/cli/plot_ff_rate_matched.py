"""CLI: Visualise ff_rate_matched vs ASAP vs stall_aware_shifted_refined."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Plot ff_rate_matched experiment results")
    parser.add_argument("--analysis-dir", type=Path, required=True)
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

    with (args.analysis_dir / "policy_width_summary.csv").open() as fh:
        rows = list(csv.DictReader(fh))

    ff_widths = [4, 5, 6, 7, 8]
    algorithms = ["QAOA", "QFT", "VQE"]
    policies = ["asap", "ff_rate_matched", "stall_aware_shifted_refined"]
    policy_labels = {
        "asap": "ASAP (baseline)",
        "ff_rate_matched": "ff_rate_matched (new)",
        "stall_aware_shifted_refined": "stall_aware_shifted_refined",
    }

    alg_colors = {"QAOA": "#1565C0", "QFT": "#C62828", "VQE": "#2E7D32"}
    policy_color = {
        "asap": "#888888",
        "ff_rate_matched": "#E65100",
        "stall_aware_shifted_refined": "#6A1B9A",
    }
    policy_ls = {
        "asap": "--",
        "ff_rate_matched": "-",
        "stall_aware_shifted_refined": ":",
    }
    policy_marker = {
        "asap": "o",
        "ff_rate_matched": "D",
        "stall_aware_shifted_refined": "s",
    }
    policy_lw = {
        "asap": 1.5,
        "ff_rate_matched": 2.5,
        "stall_aware_shifted_refined": 1.5,
    }

    def _get(alg: str, policy: str, ff_w: int, metric: str) -> float | None:
        for r in rows:
            if (r["algorithm"] == alg
                    and r["policy"] == policy
                    and r["width_profile"] == f"W8_M8_F{ff_w}"):
                return float(r[metric])
        return None

    def _fstar(alg: str, policy: str) -> int | None:
        for fw in ff_widths:
            v = _get(alg, policy, fw, "stall_reduction_pct_median")
            if v is not None and v >= 0:
                return fw
        return None

    # ── Fig 1: Stall reduction per algorithm ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), sharey=False)
    fig.suptitle(
        "Stall reduction (shifted vs raw) by ff_width — ff_rate_matched eliminates stall regression\n"
        "Positive = stall improved; Negative = stall regression (shifted DAG hurt more than raw)",
        fontsize=12,
    )
    for ax, alg in zip(axes, algorithms):
        ax.axhline(0, color="black", lw=1.5, linestyle="--", alpha=0.8, label="break-even (0%)")
        ax.fill_between(ff_widths, -2000, 0, alpha=0.06, color="red", label="_nolegend_")
        for policy in policies:
            ys = [_get(alg, policy, fw, "stall_reduction_pct_median") for fw in ff_widths]
            ys_clean = [y if y is not None else float("nan") for y in ys]
            ax.plot(
                ff_widths, ys_clean,
                color=policy_color[policy],
                ls=policy_ls[policy],
                marker=policy_marker[policy],
                markersize=8,
                lw=policy_lw[policy],
                label=policy_labels[policy],
                alpha=0.95,
                zorder=3 if policy == "ff_rate_matched" else 2,
            )
            # Annotate F*
            fs = _fstar(alg, policy)
            if fs is not None and policy == "ff_rate_matched":
                ax.axvline(fs, color=policy_color[policy], lw=1.0, ls=":", alpha=0.5)
                y_pos = _get(alg, policy, fs, "stall_reduction_pct_median") or 50
                ax.annotate(
                    f"F*={fs}",
                    xy=(fs, y_pos),
                    xytext=(fs + 0.15, y_pos + 5),
                    fontsize=9,
                    color=policy_color[policy],
                    fontweight="bold",
                )

        ax.set_title(alg, fontsize=13, color=alg_colors[alg], fontweight="bold")
        ax.set_xlabel("ff_width", fontsize=11)
        ax.set_ylabel("Stall reduction % (raw→shifted)" if alg == "QAOA" else "", fontsize=10)
        ax.set_xticks(ff_widths)
        ax.legend(fontsize=9, loc="lower right")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_ffrm_stall_reduction.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 2: Throughput gain comparison ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), sharey=False)
    fig.suptitle(
        "Throughput gain (shifted vs raw) by ff_width\n"
        "ff_rate_matched matches ASAP throughput while eliminating stall regression",
        fontsize=12,
    )
    for ax, alg in zip(axes, algorithms):
        ax.axhline(0, color="black", lw=1.0, linestyle="--", alpha=0.5)
        for policy in policies:
            ys = [_get(alg, policy, fw, "throughput_gain_pct_median") for fw in ff_widths]
            ys_clean = [y if y is not None else float("nan") for y in ys]
            ax.plot(
                ff_widths, ys_clean,
                color=policy_color[policy],
                ls=policy_ls[policy],
                marker=policy_marker[policy],
                markersize=8,
                lw=policy_lw[policy],
                label=policy_labels[policy],
                alpha=0.95,
                zorder=3 if policy == "ff_rate_matched" else 2,
            )
        ax.set_title(alg, fontsize=13, color=alg_colors[alg], fontweight="bold")
        ax.set_xlabel("ff_width", fontsize=11)
        ax.set_ylabel("Throughput gain % (raw→shifted)" if alg == "QAOA" else "", fontsize=10)
        ax.set_xticks(ff_widths)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_ffrm_throughput_gain.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Fig 3: Summary bar chart — F* per algorithm × policy ──
    fig, ax = plt.subplots(figsize=(10, 5))
    bar_width = 0.25
    x = np.arange(len(algorithms))
    for i, policy in enumerate(policies):
        fstars = [_fstar(alg, policy) or 9 for alg in algorithms]
        bars = ax.bar(
            x + i * bar_width,
            fstars,
            bar_width,
            label=policy_labels[policy],
            color=policy_color[policy],
            alpha=0.85,
            edgecolor="white",
        )
        for bar, fs in zip(bars, fstars):
            label = str(fs) if fs <= 8 else ">8"
            ax.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center", va="bottom", fontsize=10, fontweight="bold",
                color=policy_color[policy],
            )

    ax.set_title(
        "F* (minimum ff_width for zero stall regression)\n"
        "Lower is better — ff_rate_matched achieves F*=4 on all algorithms",
        fontsize=12,
    )
    ax.set_xticks(x + bar_width)
    ax.set_xticklabels(algorithms, fontsize=12)
    ax.set_ylabel("F* (minimum ff_width)", fontsize=11)
    ax.set_yticks(ff_widths)
    ax.set_ylim(0, 10)
    ax.axhline(4, color="orange", lw=1.5, ls=":", alpha=0.6, label="F=4 (minimum tested)")
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    out = args.output_dir / "fig_ffrm_fstar_summary.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # ── Print F* summary table ──
    print("\n=== F* Summary: minimum ff_width for stall improvement ===")
    print(f"{'Alg':<6} {'Policy':<35} {'F4':>7} {'F5':>7} {'F6':>7} {'F7':>7} {'F8':>7}  F*")
    for alg in algorithms:
        for policy in policies:
            vals = [_get(alg, policy, fw, "stall_reduction_pct_median") for fw in ff_widths]
            fs = _fstar(alg, policy)
            vs = "  ".join(f"{v:>6.1f}" if v is not None else "   N/A" for v in vals)
            print(f"  {alg:<4} {policy:<35} {vs}  F*={fs if fs else '>8'}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()
