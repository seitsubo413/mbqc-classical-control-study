"""
gen_fig6.py — Generate Figure 6: F* sensitivity heatmap (Studies 18 & 19)

Updated in draft_v7 to include F=2 and F=3 in the raw-ASAP baseline
using Study 21 data, which extends the raw-DAG sweep to ff_width in {2,3,4}.

Left panel:  F*(ff_rate_matched) vs L_ff × algorithm  (Study 18 + Study 21 baseline)
Right panel: F*(ff_rate_matched) vs L_meas × algorithm+hq_pair (Study 19 + Study 21 baseline)

F*(policy) = min F such that stall_rate(shifted, policy, F) <= stall_rate(raw, ASAP, F)

Filter: issue_width=8, meas_width=8, release_mode=next_cycle
Aggregate over seeds (median).
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch

STUDY18_CSV = (
    "/Users/seitsubo/Project/mbqc-classical-control-study/"
    "research/mbqc_pipeline_sim/results/studies/"
    "18_lff_sensitivity/summary/sweep.csv"
)
STUDY19_CSV = (
    "/Users/seitsubo/Project/mbqc-classical-control-study/"
    "research/mbqc_pipeline_sim/results/studies/"
    "19_lmeas_sensitivity/summary/sweep_all.csv"
)
STUDY21_CSV = (
    "/Users/seitsubo/Project/mbqc-classical-control-study/"
    "research/mbqc_pipeline_sim/results/studies/"
    "21_raw_low_ffwidth/summary/sweep.csv"
)
OUT_PNG = (
    "/Users/seitsubo/Project/mbqc-classical-control-study/"
    "docs/paper/figures/fig6_sensitivity.png"
)

# ---------------------------------------------------------------------------
# Helper: compute F* for a given group
#   group contains rows for both raw+ASAP and shifted+policy at various F
# ---------------------------------------------------------------------------

def compute_fstar(df_raw_asap, df_shifted_policy, ff_widths):
    """Return minimum F where shifted_policy stall <= raw_asap stall."""
    for F in sorted(ff_widths):
        raw_rows   = df_raw_asap[df_raw_asap["ff_width"] == F]["stall_rate"]
        shift_rows = df_shifted_policy[df_shifted_policy["ff_width"] == F]["stall_rate"]
        if len(raw_rows) == 0 or len(shift_rows) == 0:
            continue
        raw_med   = raw_rows.median()
        shift_med = shift_rows.median()
        if shift_med <= raw_med:
            return F
    return max(ff_widths)   # not found → worst


# ---------------------------------------------------------------------------
# Load Study 21 raw+ASAP baseline (F=2,3,4)
# ---------------------------------------------------------------------------

df21 = pd.read_csv(STUDY21_CSV)
df21 = df21[
    (df21["issue_width"] == 8) &
    (df21["meas_width"] == 8) &
    (df21["release_mode"] == "next_cycle") &
    (df21["dag_variant"] == "raw") &
    (df21["policy"] == "asap")
].copy()

# ---------------------------------------------------------------------------
# Study 18: F* vs L_ff × algorithm
# Now use Study 21 raw+ASAP baseline at F in {2,3,4} and Study 18 shifted at F in {4,6,8}
# The union of F values for the comparison: {2,3,4} (we use the Study 21 raw baseline
# matched at F=4, which is the overlap point)
# For F=2,3: use Study 21 raw; for F=4,6,8: use Study 18 raw
# ---------------------------------------------------------------------------

df18 = pd.read_csv(STUDY18_CSV)

# Filter: issue_width=8, meas_width=8, release_mode=next_cycle
df18 = df18[
    (df18["issue_width"] == 8) &
    (df18["meas_width"] == 8) &
    (df18["release_mode"] == "next_cycle")
].copy()

# We need raw+ASAP and shifted+{asap, ff_rate_matched} rows
df18_raw_asap = df18[(df18["dag_variant"] == "raw") & (df18["policy"] == "asap")]
df18_shifted_ffrm = df18[(df18["dag_variant"] == "shifted") & (df18["policy"] == "ff_rate_matched")]
df18_shifted_asap = df18[(df18["dag_variant"] == "shifted") & (df18["policy"] == "asap")]

lff_vals   = sorted(df18["l_ff"].unique())
algos_18   = ["QAOA", "VQE"]

# Study 18 has shifted at F in {4,6,8}; Study 21 provides raw+ASAP at F in {2,3,4}
# For F*(ff_rm): check against Study 21 raw baseline at F=2,3,4 first,
# then fall back to Study 18 raw baseline for larger F
# F* computed over the union of available F values in ascending order: 2, 3, 4, 6, 8

def compute_fstar_combined(df21_raw, df18_raw, df_shifted, algo, lff=None, hsize=None, lmeas=None):
    """Compute F* using Study 21 baseline at F=2,3 and Study 18 baseline at F=4,6,8."""
    # Build augmented raw+ASAP rows from Study 21 (F=2,3) + Study 18 (F=4)
    if algo is not None:
        raw21 = df21_raw[df21_raw["algorithm"] == algo].copy()
        raw18 = df18_raw[df18_raw["algorithm"] == algo].copy() if df18_raw is not None else pd.DataFrame()
    else:
        raw21 = df21_raw.copy()
        raw18 = df18_raw.copy() if df18_raw is not None else pd.DataFrame()

    if lff is not None:
        raw18 = raw18[raw18["l_ff"] == lff] if len(raw18) > 0 else raw18
        shifted = df_shifted[(df_shifted["algorithm"] == algo) & (df_shifted["l_ff"] == lff)]
    elif lmeas is not None and hsize is not None:
        raw18 = raw18[(raw18["hardware_size"] == hsize) & (raw18["l_meas"] == lmeas)] if len(raw18) > 0 else raw18
        shifted = df_shifted[(df_shifted["algorithm"] == algo) & (df_shifted["hardware_size"] == hsize) & (df_shifted["l_meas"] == lmeas)]
    else:
        shifted = df_shifted[df_shifted["algorithm"] == algo]

    # Filter raw21 by algo (already done)
    # Check F in ascending order: 2, 3, 4, 6, 8
    all_F = [2, 3, 4, 6, 8]
    for F in all_F:
        # Get raw stall at F
        raw_rows_21 = raw21[raw21["ff_width"] == F]["stall_rate"]
        raw_rows_18 = raw18[raw18["ff_width"] == F]["stall_rate"] if len(raw18) > 0 else pd.Series()
        raw_rows = pd.concat([raw_rows_21, raw_rows_18])
        shift_rows = shifted[shifted["ff_width"] == F]["stall_rate"]
        if len(raw_rows) == 0 or len(shift_rows) == 0:
            continue
        if shift_rows.median() <= raw_rows.median():
            return F
    return 8

# Build matrices: rows=algo, cols=l_ff
fstar_ffrm_18 = {}
fstar_asap_18 = {}
for algo in algos_18:
    fstar_ffrm_18[algo] = []
    fstar_asap_18[algo] = []
    for lff in lff_vals:
        f_ffrm = compute_fstar_combined(df21, df18_raw_asap, df18_shifted_ffrm, algo, lff=lff)
        f_asap = compute_fstar_combined(df21, df18_raw_asap, df18_shifted_asap, algo, lff=lff)
        fstar_ffrm_18[algo].append(f_ffrm)
        fstar_asap_18[algo].append(f_asap)

mat_ffrm_18 = np.array([fstar_ffrm_18[a] for a in algos_18])   # (2, n_lff)
mat_asap_18 = np.array([fstar_asap_18[a] for a in algos_18])

# ---------------------------------------------------------------------------
# Study 19: F* vs L_meas × algorithm+hq_pair
# ---------------------------------------------------------------------------

df19 = pd.read_csv(STUDY19_CSV)

df19 = df19[
    (df19["issue_width"] == 8) &
    (df19["meas_width"] == 8) &
    (df19["release_mode"] == "next_cycle")
].copy()

df19_raw_asap = df19[(df19["dag_variant"] == "raw") & (df19["policy"] == "asap")]
df19_shifted_ffrm = df19[(df19["dag_variant"] == "shifted") & (df19["policy"] == "ff_rate_matched")]
df19_shifted_asap = df19[(df19["dag_variant"] == "shifted") & (df19["policy"] == "asap")]

lmeas_vals = sorted(df19["l_meas"].unique())
ff_widths_19 = sorted(df19["ff_width"].unique())

# hq_pairs present in study 19
hq_pairs_19 = [
    ("QAOA", 6),
    ("QAOA", 8),
    ("VQE",  6),
    ("VQE",  8),
]
row_labels_19 = ["QAOA H6", "QAOA H8", "VQE H6", "VQE H8"]

fstar_ffrm_19 = []
fstar_asap_19 = []
for (algo, hsize) in hq_pairs_19:
    row_ffrm = []
    row_asap = []
    for lmeas in lmeas_vals:
        f_ffrm = compute_fstar_combined(df21, df19_raw_asap, df19_shifted_ffrm, algo, hsize=hsize, lmeas=lmeas)
        f_asap = compute_fstar_combined(df21, df19_raw_asap, df19_shifted_asap, algo, hsize=hsize, lmeas=lmeas)
        row_ffrm.append(f_ffrm)
        row_asap.append(f_asap)
    fstar_ffrm_19.append(row_ffrm)
    fstar_asap_19.append(row_asap)

mat_ffrm_19 = np.array(fstar_ffrm_19)   # (4, n_lmeas)
mat_asap_19 = np.array(fstar_asap_19)

# ---------------------------------------------------------------------------
# Color map: 2=dark-green, 3=light-green, 4=green, 5-6=yellow, 7=orange, 8=red
# ---------------------------------------------------------------------------

CMAP_BOUNDS = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]
# F*=2 dark green, F*=3 medium green, F*=4 green (W/2), F*=5 yellow-green,
# F*=6 orange, F*=7 red-orange, F*=8 dark red
CMAP_COLORS = ["#1a7a1a", "#44b944", "#2ca02c", "#bcbd22", "#ff7f0e", "#d62728", "#8c0b0b"]
cmap = mcolors.ListedColormap(CMAP_COLORS)
norm = mcolors.BoundaryNorm(CMAP_BOUNDS, cmap.N)

def draw_heatmap(ax, mat, xticklabels, yticklabels, xlabel, ylabel, title,
                 label_prefix="F* = "):
    im = ax.imshow(mat, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(xticklabels)))
    ax.set_xticklabels(xticklabels, fontsize=10)
    ax.set_yticks(range(len(yticklabels)))
    ax.set_yticklabels(yticklabels, fontsize=10)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=11, fontweight="bold")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = mat[i, j]
            txt_color = "white" if val >= 7 else "black"
            ax.text(j, i, f"{val}", ha="center", va="center",
                    fontsize=13, fontweight="bold", color=txt_color)
    return im

# ---------------------------------------------------------------------------
# 4-panel figure: top row = ff_rate_matched, bottom row = ASAP (contrast)
# Columns: Study 18 (L_ff), Study 19 (L_meas)
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(2, 2, figsize=(13, 7))
fig.suptitle(
    "F* sensitivity (Study 21 raw baseline extends sweep to F=2,3)\n"
    "ff_rate_matched (top): F*(ff_rm) = 4 in Studies 18/19 context (F>=4 swept)\n"
    "Direct F*=2 confirmation: Study 20 shifted+ff_rm (F=2,3,4) vs Study 21 raw+ASAP",
    fontsize=11, fontweight="bold", y=1.02
)

# --- top-left: ff_rate_matched, Study 18 (L_ff)
draw_heatmap(
    axes[0, 0],
    mat_ffrm_18,
    xticklabels=[str(v) for v in lff_vals],
    yticklabels=algos_18,
    xlabel="FF latency L_ff",
    ylabel="Algorithm",
    title="ff_rate_matched: F*(ff_rm) vs L_ff\n(Study 18, W=8, Study 21 baseline)",
)

# --- top-right: ff_rate_matched, Study 19 (L_meas)
draw_heatmap(
    axes[0, 1],
    mat_ffrm_19,
    xticklabels=[str(v) for v in lmeas_vals],
    yticklabels=row_labels_19,
    xlabel="Measurement latency L_meas",
    ylabel="Algorithm + H",
    title="ff_rate_matched: F*(ff_rm) vs L_meas\n(Study 19, W=8, Study 21 baseline)",
)

# --- bottom-left: ASAP, Study 18
draw_heatmap(
    axes[1, 0],
    mat_asap_18,
    xticklabels=[str(v) for v in lff_vals],
    yticklabels=algos_18,
    xlabel="FF latency L_ff",
    ylabel="Algorithm",
    title="ASAP: F*(ASAP) vs L_ff\n(Study 18, W=8)",
)

# --- bottom-right: ASAP, Study 19
draw_heatmap(
    axes[1, 1],
    mat_asap_19,
    xticklabels=[str(v) for v in lmeas_vals],
    yticklabels=row_labels_19,
    xlabel="Measurement latency L_meas",
    ylabel="Algorithm + H",
    title="ASAP: F*(ASAP) vs L_meas\n(Study 19, W=8)",
)

# Legend
legend_elements = [
    Patch(facecolor="#1a7a1a", label="F* = 2 (confirmed minimum)"),
    Patch(facecolor="#44b944", label="F* = 3"),
    Patch(facecolor="#2ca02c", label="F* = 4 (W/2 design point)"),
    Patch(facecolor="#bcbd22", label="F* = 5 (yellow-green)"),
    Patch(facecolor="#ff7f0e", label="F* = 6 (orange)"),
    Patch(facecolor="#d62728", label="F* = 7 (red-orange)"),
    Patch(facecolor="#8c0b0b", label="F* = 8 (= W, worst, dark red)"),
]
fig.legend(handles=legend_elements, loc="lower center", ncol=4, fontsize=9,
           bbox_to_anchor=(0.5, -0.08))

plt.tight_layout(rect=[0, 0.09, 1, 1])
plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
print(f"Saved: {OUT_PNG}")

# Print computed matrices for verification
print("\n--- Study 18: F*(ff_rate_matched) ---")
for i, algo in enumerate(algos_18):
    print(f"  {algo}: {list(mat_ffrm_18[i])}")
print("\n--- Study 18: F*(ASAP) ---")
for i, algo in enumerate(algos_18):
    print(f"  {algo}: {list(mat_asap_18[i])}")
print("\n--- Study 19: F*(ff_rate_matched) ---")
for i, label in enumerate(row_labels_19):
    print(f"  {label}: {list(mat_ffrm_19[i])}")
print("\n--- Study 19: F*(ASAP) ---")
for i, label in enumerate(row_labels_19):
    print(f"  {label}: {list(mat_asap_19[i])}")
