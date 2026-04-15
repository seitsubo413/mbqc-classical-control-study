"""Plot builders for publication figures."""

from __future__ import annotations

import math
import os
from collections import defaultdict
from pathlib import Path
from typing import cast

_PLOT_CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache" / "matplotlib"
_PLOT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_PLOT_CACHE_DIR))

import matplotlib
from matplotlib.axes import Axes

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from mbqc_ff_evaluator.analysis.models import BudgetRow, BudgetSelection, MetricsRow
from mbqc_ff_evaluator.analysis.selection import filter_budget_rows, selection_label
from mbqc_ff_evaluator.domain.enums import ConstraintKind

ALGO_COLORS: dict[str, str] = {
    "QAOA": "#1f77b4",
    "QFT": "#ff7f0e",
    "VQE": "#2ca02c",
    "Grover": "#d62728",
    "RCA": "#9467bd",
}

H_MARKERS: dict[int, str] = {
    4: "o",
    6: "s",
    8: "^",
    10: "D",
    12: "v",
    14: "P",
    16: "*",
}

CONSTRAINT_STYLES: dict[ConstraintKind, tuple[str, str]] = {
    ConstraintKind.DEPENDENCY: ("#1f77b4", "o-"),
    ConstraintKind.HOLD: ("#2ca02c", "s--"),
    ConstraintKind.MEASUREMENT: ("#d62728", "D-."),
}

REFERENCE_LINES_NS = [200.0, 250.0]


def plot_figure1_divergence(
    metrics: list[MetricsRow],
    output_path: Path,
) -> Path:
    fig, ax = plt.subplots(figsize=(7, 6))

    for row in metrics:
        if row.status != "success" or row.required_lifetime_layers is None:
            continue
        color = ALGO_COLORS.get(row.algorithm, "#888888")
        marker = H_MARKERS.get(row.hardware_size, "o")
        ax.scatter(
            row.required_lifetime_layers,
            row.ff_chain_depth_raw,
            c=color,
            marker=marker,
            s=40,
            alpha=0.7,
            edgecolors="white",
            linewidths=0.5,
        )

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    diag_max = max(xmax, ymax)
    ax.plot([0, diag_max], [0, diag_max], "k--", alpha=0.3, label="y = x")

    _add_algo_legend(ax, metrics)
    _add_h_legend(ax, metrics)

    ax.set_xlim(left=min(0.0, xmin), right=diag_max)
    ax.set_ylim(bottom=min(0.0, ymin), top=diag_max)
    ax.set_xlabel("required_lifetime_layers (L_hold)")
    ax.set_ylabel("ff_chain_depth_raw (D_ff)")
    ax.set_title("Figure 1: Metric Divergence – L_hold vs D_ff")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_figure2_main_budget(
    budgets: list[BudgetRow],
    output_path: Path,
    selection: BudgetSelection,
) -> Path:
    fig, ax = plt.subplots(figsize=(8, 6))
    title_suffix = selection_label(selection)

    algo_data = _group_budget_rows(budgets, selection)
    for algo, rows in sorted(algo_data.items()):
        qs = [row.logical_qubits for row in rows]
        medians = [row.t_ff_cond_ns_median for row in rows]
        q1s = [row.t_ff_cond_ns_q1 for row in rows]
        q3s = [row.t_ff_cond_ns_q3 for row in rows]
        color = ALGO_COLORS.get(algo, "#888888")
        ax.plot(qs, medians, "o-", color=color, label=algo, markersize=5)
        ax.fill_between(qs, q1s, q3s, color=color, alpha=0.15)

    _add_reference_lines(ax)
    ax.set_xlabel("Logical Qubits (Q)")
    ax.set_ylabel("t_ff_cond_ns (median ± IQR)")
    ax.set_title(f"Figure 2: Raw Dependency Budget – {title_suffix}")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_figure3_triplet_budgets(
    budgets: list[BudgetRow],
    output_path: Path,
    selection: BudgetSelection,
) -> Path:
    algo_data = _group_budget_rows(budgets, selection)
    algorithms = sorted(algo_data)
    fig, axes = plt.subplots(
        nrows=len(algorithms),
        ncols=1,
        figsize=(8, max(3.5 * len(algorithms), 4.0)),
        sharex=True,
    )
    if len(algorithms) == 1:
        axes = [axes]

    for ax, algo in zip(axes, algorithms):
        rows = algo_data[algo]
        qs = [row.logical_qubits for row in rows]
        dep = [row.t_ff_cond_ns_median for row in rows]
        hold = [row.t_hold_ns_median for row in rows]
        meas = [row.t_meas_ns_median for row in rows]

        ax.plot(qs, dep, CONSTRAINT_STYLES[ConstraintKind.DEPENDENCY][1], color=CONSTRAINT_STYLES[ConstraintKind.DEPENDENCY][0], label="dependency")
        ax.plot(qs, hold, CONSTRAINT_STYLES[ConstraintKind.HOLD][1], color=CONSTRAINT_STYLES[ConstraintKind.HOLD][0], label="hold")
        ax.plot(qs, meas, CONSTRAINT_STYLES[ConstraintKind.MEASUREMENT][1], color=CONSTRAINT_STYLES[ConstraintKind.MEASUREMENT][0], label="measurement")
        _add_reference_lines(ax)
        ax.set_yscale("log")
        ax.set_ylabel(f"{algo}\nbudget (ns)")
        ax.grid(True, alpha=0.3, which="both")
        ax.legend(loc="best")

    axes[-1].set_xlabel("Logical Qubits (Q)")
    fig.suptitle(f"Figure 3: Dependency / Hold / Measurement Comparison – {selection_label(selection)}", y=0.995)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_figure4_shifted_budget(
    budgets: list[BudgetRow],
    output_path: Path,
    selection: BudgetSelection,
) -> Path:
    fig, ax = plt.subplots(figsize=(8, 6))

    algo_data = _group_budget_rows(budgets, selection)
    for algo, rows in sorted(algo_data.items()):
        usable = [row for row in rows if row.t_ff_shifted_ns_median is not None]
        if not usable:
            continue
        qs = [row.logical_qubits for row in usable]
        medians = [cast(float, row.t_ff_shifted_ns_median) for row in usable]
        q1s = [cast(float, row.t_ff_shifted_ns_q1) for row in usable]
        q3s = [cast(float, row.t_ff_shifted_ns_q3) for row in usable]
        color = ALGO_COLORS.get(algo, "#888888")
        ax.plot(qs, medians, "o-", color=color, label=algo, markersize=5)
        ax.fill_between(qs, q1s, q3s, color=color, alpha=0.15)

    _add_reference_lines(ax)
    ax.set_xlabel("Logical Qubits (Q)")
    ax.set_ylabel("t_ff_shifted_ns (median ± IQR)")
    ax.set_title(f"Figure 4: Shifted Dependency Budget – {selection_label(selection)}")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_figure5_lifetime_sensitivity(
    budgets: list[BudgetRow],
    output_path: Path,
    selection: BudgetSelection,
    algorithm: str | None = None,
) -> Path:
    algorithms = [algorithm] if algorithm is not None else sorted({row.algorithm for row in budgets})
    fig, axes = plt.subplots(
        nrows=len(algorithms),
        ncols=1,
        figsize=(8, max(3.5 * len(algorithms), 4.0)),
        sharex=True,
    )
    if len(algorithms) == 1:
        axes = [axes]

    tau_styles = {0.5: "--", 1.0: "-", 5.0: "-."}
    tau_colors = {0.5: "#e41a1c", 1.0: "#377eb8", 5.0: "#4daf4a"}

    for ax, algo_name in zip(axes, algorithms):
        filtered = [
            row
            for row in budgets
            if row.algorithm == algo_name and _matches_selection_without_tau(row, selection)
        ]
        tau_groups: dict[float, list[BudgetRow]] = defaultdict(list)
        for row in filtered:
            tau_groups[row.tau_ph_us].append(row)
        for tau, rows in sorted(tau_groups.items()):
            rows.sort(key=lambda row: row.logical_qubits)
            qs = [row.logical_qubits for row in rows]
            vals = [row.t_ff_cond_ns_median for row in rows]
            ax.plot(
                qs,
                vals,
                f"o{tau_styles.get(tau, '-')}",
                color=tau_colors.get(tau, "#888888"),
                label=f"τ = {tau} μs",
                markersize=5,
            )
        _add_reference_lines(ax)
        ax.set_ylabel(f"{algo_name}\nt_ff_cond_ns")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")

    axes[-1].set_xlabel("Logical Qubits (Q)")
    fig.suptitle(f"Figure 5: Photon Lifetime Sensitivity – {selection_label(selection)}", y=0.995)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_figure6_reference_depth(
    budgets: list[BudgetRow],
    output_path: Path,
    selection: BudgetSelection,
) -> Path:
    reference_rows = [
        row
        for row in filter_budget_rows(budgets, selection)
        if row.depth_reference_median is not None
    ]
    reference_rows.sort(key=lambda row: (row.algorithm, row.hardware_size, row.logical_qubits))

    fig, ax = plt.subplots(figsize=(8, 5))
    if not reference_rows:
        ax.text(0.5, 0.5, "No reference-depth rows available", ha="center", va="center")
        ax.set_axis_off()
    else:
        positions = list(range(len(reference_rows)))
        width = 0.24
        labels = [f"{row.algorithm}\nH={row.hardware_size}, Q={row.logical_qubits}" for row in reference_rows]
        raw_vals = [row.depth_raw_median for row in reference_rows]
        shifted_vals = [cast(float, row.depth_shifted_median) for row in reference_rows]
        reference_vals = [cast(float, row.depth_reference_median) for row in reference_rows]

        ax.bar([pos - width for pos in positions], raw_vals, width=width, label="raw depth", color="#1f77b4")
        ax.bar([pos for pos in positions], shifted_vals, width=width, label="shifted depth", color="#2ca02c")
        ax.bar([pos + width for pos in positions], reference_vals, width=width, label="graphix reference", color="#d62728")
        ax.set_yscale("log")
        ax.set_xticks(positions)
        ax.set_xticklabels(labels)
        ax.set_ylabel("depth")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3, axis="y", which="both")

    ax.set_title(f"Figure 6: Small-Scale Independent Reference Depth – {selection_label(selection)}")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_figure7_hardware_width_effect(
    budgets: list[BudgetRow],
    output_path: Path,
    *,
    algorithm: str = "QAOA",
    tau_ph_us: float = 1.0,
) -> Path:
    rows = [
        row
        for row in budgets
        if row.algorithm == algorithm and abs(row.tau_ph_us - tau_ph_us) <= 0.01
    ]
    grouped: dict[int, list[BudgetRow]] = defaultdict(list)
    for row in rows:
        grouped[row.logical_qubits].append(row)

    fixed_qs = sorted(q for q, group in grouped.items() if len(group) >= 2)
    if not fixed_qs:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No fixed-Q hardware-width data available", ha="center", va="center")
        ax.set_axis_off()
        fig.tight_layout()
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return output_path

    fig, axes = plt.subplots(
        nrows=len(fixed_qs),
        ncols=1,
        figsize=(8, max(3.5 * len(fixed_qs), 4.0)),
        sharex=False,
    )
    if len(fixed_qs) == 1:
        axes = [axes]

    for ax, logical_qubits in zip(axes, fixed_qs):
        group = sorted(grouped[logical_qubits], key=lambda row: row.hardware_size)
        hs = [row.hardware_size for row in group]
        depths = [row.depth_raw_median for row in group]
        holds = [row.hold_median for row in group if row.hold_median is not None]
        hold_hs = [row.hardware_size for row in group if row.hold_median is not None]

        ax.plot(hs, depths, "o-", color=CONSTRAINT_STYLES[ConstraintKind.DEPENDENCY][0], label="D_ff")
        ax.plot(hold_hs, holds, "s--", color=CONSTRAINT_STYLES[ConstraintKind.HOLD][0], label="L_hold")
        ax.set_ylabel(f"Q={logical_qubits}\ndepth / layers")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")

    axes[-1].set_xlabel("Hardware Size (H)")
    fig.suptitle(f"Figure 7: Hardware Width Effect – {algorithm}, τ={tau_ph_us} μs", y=0.995)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_appendix_conservative(
    budgets: list[BudgetRow],
    output_path: Path,
    selection: BudgetSelection,
) -> Path:
    fig, ax = plt.subplots(figsize=(8, 6))

    algo_data = _group_budget_rows(budgets, selection)
    for algo, rows in sorted(algo_data.items()):
        usable = [row for row in rows if row.t_cons_ns_median is not None]
        if not usable:
            continue
        qs = [row.logical_qubits for row in usable]
        cons = [cast(float, row.t_cons_ns_median) for row in usable]
        color = ALGO_COLORS.get(algo, "#888888")
        ax.plot(qs, cons, "o-", color=color, label=f"{algo} (t_cons)", markersize=5)

    _add_reference_lines(ax)
    ax.set_xlabel("Logical Qubits (Q)")
    ax.set_ylabel("t_cons_ns (median)")
    ax.set_title(f"Appendix: Conservative Budget – {selection_label(selection)}")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _group_budget_rows(
    budgets: list[BudgetRow],
    selection: BudgetSelection,
) -> dict[str, list[BudgetRow]]:
    algo_data: dict[str, list[BudgetRow]] = defaultdict(list)
    for row in filter_budget_rows(budgets, selection):
        if math.isinf(row.t_ff_cond_ns_median):
            continue
        algo_data[row.algorithm].append(row)
    for rows in algo_data.values():
        rows.sort(key=lambda item: item.logical_qubits)
    return algo_data


def _matches_selection_without_tau(row: BudgetRow, selection: BudgetSelection) -> bool:
    trial_selection = BudgetSelection(
        mode=selection.mode,
        tau_ph_us=row.tau_ph_us,
        hardware_size=selection.hardware_size,
        logical_qubits=selection.logical_qubits,
    )
    return bool(filter_budget_rows([row], trial_selection))


def _add_reference_lines(ax: Axes) -> None:
    for ref_ns in REFERENCE_LINES_NS:
        ax.axhline(ref_ns, color="gray", linestyle=":", alpha=0.5)


def _add_algo_legend(ax: Axes, metrics: list[MetricsRow]) -> None:
    algos = sorted({row.algorithm for row in metrics})
    handles = []
    for algo in algos:
        color = ALGO_COLORS.get(algo, "#888888")
        handles.append(ax.scatter([], [], c=color, s=40, label=algo))
    legend1 = ax.legend(handles=handles, loc="upper left", title="Algorithm")
    ax.add_artist(legend1)


def _add_h_legend(ax: Axes, metrics: list[MetricsRow]) -> None:
    h_vals = sorted({row.hardware_size for row in metrics})
    handles = []
    for hv in h_vals:
        marker = H_MARKERS.get(hv, "o")
        handles.append(ax.scatter([], [], c="gray", marker=marker, s=40, label=f"H={hv}"))
    ax.legend(handles=handles, loc="lower right", title="Hardware Size")
