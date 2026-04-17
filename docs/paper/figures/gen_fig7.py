"""
gen_fig7.py — Generate Figure 7: H=10/12 scaling results (Study 20)

2×2 panel figure:
  Rows:    QAOA (top), VQE (bottom)
  Columns: H=10 (left), H=12 (right, Q=64 only)

For each panel: x=ff_width (2,3,4), y=stall_rate
  - Median over seeds × issue_widths
  - Two lines: ASAP (gray dashed) and ff_rate_matched (orange solid)
  - Green dashed horizontal line at raw+ASAP baseline (~3.45% QAOA, ~0.86% VQE)
  - Vertical dashed line at ff_width=4 labelled "F* = 4"
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STUDY20_CSV = (
    "/Users/seitsubo/Project/mbqc-classical-control-study/"
    "research/mbqc_pipeline_sim/results/studies/"
    "20_large_scale_h10_h12/summary/sweep.csv"
)
OUT_PNG = (
    "/Users/seitsubo/Project/mbqc-classical-control-study/"
    "docs/paper/figures/fig7_scaling.png"
)

# Raw+ASAP baseline stall rates (Study 18, W=8, F=4, L_ff=2, median over seeds)
BASELINE_STALL = {
    "QAOA": 0.0345,   # 3.45%
    "VQE":  0.0086,   # 0.86%
}

# -------------------------------------------------------------------------
# Load data
# -------------------------------------------------------------------------
df = pd.read_csv(STUDY20_CSV)

# Keep only shifted DAG with release_mode=next_cycle
df = df[
    (df["dag_variant"] == "shifted") &
    (df["release_mode"] == "next_cycle")
].copy()

ff_widths = [2, 3, 4]

# -------------------------------------------------------------------------
# Helper: compute median stall_rate for a condition
# -------------------------------------------------------------------------
def get_stall(df_sub, algo, hsize, qsize, policy, ff_w):
    mask = (
        (df_sub["algorithm"] == algo) &
        (df_sub["hardware_size"] == hsize) &
        (df_sub["logical_qubits"] == qsize) &
        (df_sub["policy"] == policy) &
        (df_sub["ff_width"] == ff_w)
    )
    rows = df_sub[mask]["stall_rate"]
    if len(rows) == 0:
        return np.nan
    return rows.median()

# -------------------------------------------------------------------------
# Panel specification
# -------------------------------------------------------------------------
# H=10: Q in {36, 64, 100}; H=12: Q=64 only
Q_VALS_H10 = [36, 64, 100]
Q_VALS_H12 = [64]

COLORS_H10 = ["#74c0fc", "#1f77b4", "#08306b"]   # light→dark blue for Q=36,64,100
COLORS_H12 = ["#ff7f0e"]

ALGORITHMS = ["QAOA", "VQE"]

fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
fig.subplots_adjust(hspace=0.38, wspace=0.30)

for row_idx, algo in enumerate(ALGORITHMS):
    baseline = BASELINE_STALL[algo]

    # ---- left column: H=10 ----
    ax = axes[row_idx, 0]
    plotted_any = False
    for q_idx, Q in enumerate(Q_VALS_H10):
        color = COLORS_H10[q_idx]
        asap_vals = [get_stall(df, algo, 10, Q, "asap", F) for F in ff_widths]
        ffrm_vals = [get_stall(df, algo, 10, Q, "ff_rate_matched", F) for F in ff_widths]
        if not all(np.isnan(v) for v in asap_vals):
            ax.plot(ff_widths, [v * 100 for v in asap_vals],
                    color=color, linestyle="--", linewidth=1.6,
                    label=f"ASAP Q={Q}" if row_idx == 0 else None,
                    marker="o", markersize=5)
            ax.plot(ff_widths, [v * 100 for v in ffrm_vals],
                    color=color, linestyle="-", linewidth=2.0,
                    label=f"ff_rm Q={Q}" if row_idx == 0 else None,
                    marker="s", markersize=5)
            plotted_any = True

    ax.axhline(baseline * 100, color="#2ca02c", linestyle="--",
               linewidth=1.5, label="raw+ASAP baseline" if row_idx == 0 else None)
    ax.axvline(4, color="black", linestyle=":", linewidth=1.2)
    ax.text(4.05, ax.get_ylim()[1] * 0.92 if plotted_any else 5,
            "F*=4", fontsize=8, va="top")
    ax.set_title(f"{algo}, H=10", fontsize=11, fontweight="bold")
    ax.set_ylabel("Stall rate (%)", fontsize=10)
    if row_idx == 1:
        ax.set_xlabel("FF width F", fontsize=10)
    ax.set_xticks(ff_widths)
    ax.grid(True, alpha=0.3)

    # ---- right column: H=12, Q=64 ----
    ax = axes[row_idx, 1]
    for q_idx, Q in enumerate(Q_VALS_H12):
        color = COLORS_H12[q_idx]
        asap_vals = [get_stall(df, algo, 12, Q, "asap", F) for F in ff_widths]
        ffrm_vals = [get_stall(df, algo, 12, Q, "ff_rate_matched", F) for F in ff_widths]
        ax.plot(ff_widths, [v * 100 for v in asap_vals],
                color="#999999", linestyle="--", linewidth=1.8,
                label="ASAP" if row_idx == 0 else None,
                marker="o", markersize=6)
        ax.plot(ff_widths, [v * 100 for v in ffrm_vals],
                color="#ff7f0e", linestyle="-", linewidth=2.2,
                label="ff_rate_matched" if row_idx == 0 else None,
                marker="s", markersize=6)

    ax.axhline(baseline * 100, color="#2ca02c", linestyle="--",
               linewidth=1.5, label="raw+ASAP baseline" if row_idx == 0 else None)
    ax.axvline(4, color="black", linestyle=":", linewidth=1.2)
    ax.text(4.05, ax.get_ylim()[1] * 0.92 if True else 5,
            "F*=4", fontsize=8, va="top")
    ax.set_title(f"{algo}, H=12, Q=64", fontsize=11, fontweight="bold")
    if row_idx == 1:
        ax.set_xlabel("FF width F", fontsize=10)
    ax.set_xticks(ff_widths)
    ax.grid(True, alpha=0.3)

# Fix F*=4 annotation after axis limits are determined
for ax in axes.flat:
    ylim = ax.get_ylim()
    for txt in ax.texts:
        txt.set_y(ylim[1] * 0.90)

# Legend only in top-left panel
handles_labels = []
ax_tl = axes[0, 0]
# Rebuild legend for top-left
ax_tl.plot([], [], color="#74c0fc", linestyle="--", marker="o", label="ASAP, Q=36")
ax_tl.plot([], [], color="#74c0fc", linestyle="-",  marker="s", label="ff_rm, Q=36")
ax_tl.plot([], [], color="#1f77b4", linestyle="--", marker="o", label="ASAP, Q=64")
ax_tl.plot([], [], color="#1f77b4", linestyle="-",  marker="s", label="ff_rm, Q=64")
ax_tl.plot([], [], color="#08306b", linestyle="--", marker="o", label="ASAP, Q=100")
ax_tl.plot([], [], color="#08306b", linestyle="-",  marker="s", label="ff_rm, Q=100")
ax_tl.plot([], [], color="#2ca02c", linestyle="--", label="raw+ASAP baseline")

# For top-right, separate legend
ax_tr = axes[0, 1]
ax_tr.plot([], [], color="#999999", linestyle="--", marker="o", label="ASAP, Q=64")
ax_tr.plot([], [], color="#ff7f0e", linestyle="-",  marker="s", label="ff_rate_matched")
ax_tr.plot([], [], color="#2ca02c", linestyle="--", label="raw+ASAP baseline")

ax_tl.legend(fontsize=7, loc="upper right", ncol=1)
ax_tr.legend(fontsize=7, loc="upper right")

fig.suptitle(
    "Stall rate vs. FF width F for H=10 and H=12 circuits (Study 20, W=8)\n"
    "ff_rate_matched eliminates stall regression; ASAP reaches parity only at F*=4=W/2",
    fontsize=10, y=1.01
)

plt.tight_layout()
plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
print(f"Saved: {OUT_PNG}")

# Print summary values
print("\n--- Study 20 stall rates (median over seeds × issue_widths) ---")
for algo in ["QAOA", "VQE"]:
    print(f"\n{algo}:")
    for H, Q_list in [(10, Q_VALS_H10), (12, Q_VALS_H12)]:
        for Q in Q_list:
            for F in ff_widths:
                a = get_stall(df, algo, H, Q, "asap", F)
                r = get_stall(df, algo, H, Q, "ff_rate_matched", F)
                print(f"  H={H} Q={Q} F={F}  ASAP={a*100:.2f}%  ff_rm={r*100:.4f}%")
