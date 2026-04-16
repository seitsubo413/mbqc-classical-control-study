"""Publication-ready figures for MBQC pipeline simulation results."""
from __future__ import annotations

import csv
import os
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Iterable

_MPL_CONFIG_DIR = Path(__file__).resolve().parents[3] / ".mplconfig"
_MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CONFIG_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ALGO_COLORS = {"QAOA": "#1f77b4", "QFT": "#d62728", "VQE": "#2ca02c"}
ALGO_MARKERS = {"QAOA": "o", "QFT": "s", "VQE": "^"}
POLICY_STYLES = {
    "asap": "-",
    "layer": "--",
    "greedy_critical": "-.",
    "random": ":",
}
COMMON_COUPLED_PAIRS = {("4", "16"), ("6", "36"), ("8", "64")}
MAINLINE_SEEDS = {"0", "1", "2", "3", "4"}
SHIFTED_POLICIES = {"asap", "greedy_critical"}
SHIFTED_WIDTHS = {"4", "8"}
SHIFTED_LATENCIES = {"1", "2"}


def _load_csv(path: Path) -> list[dict[str, str]]:
    with open(path) as f:
        return list(csv.DictReader(f))


def _save(fig: plt.Figure, outdir: Path, name: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(outdir / f"{name}.png", dpi=200, bbox_inches="tight")
    pdf_dir = outdir / "pdf"
    pdf_dir.mkdir(exist_ok=True)
    fig.savefig(pdf_dir / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def _select_mainline_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Controlled subset used for conference-facing plots.

    Restrict to the common coupled configurations across all algorithms,
    the baseline seed set 0-4, and the optimistic unlimited-width model
    that was used for the initial sweep.
    """
    selected: list[dict[str, str]] = []
    for row in rows:
        if (row["hardware_size"], row["logical_qubits"]) not in COMMON_COUPLED_PAIRS:
            continue
        if row["dag_seed"] not in MAINLINE_SEEDS:
            continue
        if row.get("release_mode", "same_cycle") != "same_cycle":
            continue
        if row.get("meas_width", "") not in {"", None}:
            continue
        if row.get("ff_width", "") not in {"", None}:
            continue
        selected.append(row)
    return selected


def _median(values: Iterable[float]) -> float:
    return statistics.median(values)


def _select_conservative_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Conservative FF-width sweep rows.

    This helper intentionally keeps the legacy behavior of selecting only the
    next-cycle sweep where measurement width remained unlimited, because
    Figures 6/7 use that dataset as their baseline conservative sweep.
    """
    selected: list[dict[str, str]] = []
    for row in rows:
        if (row["hardware_size"], row["logical_qubits"]) not in COMMON_COUPLED_PAIRS:
            continue
        if row["dag_seed"] not in MAINLINE_SEEDS:
            continue
        if row.get("release_mode", "") != "next_cycle":
            continue
        if row.get("meas_width", "") not in {"", None}:
            continue
        selected.append(row)
    return selected


def _select_next_cycle_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Common controlled subset for next-cycle release experiments."""
    selected: list[dict[str, str]] = []
    for row in rows:
        if (row["hardware_size"], row["logical_qubits"]) not in COMMON_COUPLED_PAIRS:
            continue
        if row["dag_seed"] not in MAINLINE_SEEDS:
            continue
        if row.get("release_mode", "") != "next_cycle":
            continue
        selected.append(row)
    return selected


def _select_shifted_comparison_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Controlled subset for raw-vs-shifted dynamic comparisons."""
    selected: list[dict[str, str]] = []
    for row in rows:
        if (row["hardware_size"], row["logical_qubits"]) not in COMMON_COUPLED_PAIRS:
            continue
        if row.get("release_mode", "") != "next_cycle":
            continue
        if row.get("policy", "") not in SHIFTED_POLICIES:
            continue
        if row.get("issue_width", "") not in SHIFTED_WIDTHS:
            continue
        if row.get("l_meas", "") not in SHIFTED_LATENCIES:
            continue
        if row.get("l_ff", "") not in SHIFTED_LATENCIES:
            continue
        if row.get("meas_width", "") != row.get("issue_width", ""):
            continue
        if row.get("ff_width", "") != row.get("issue_width", ""):
            continue
        selected.append(row)
    return selected


def _pair_label(row: dict[str, str]) -> str:
    return f"H{row['hardware_size']}\nQ{row['logical_qubits']}"


def plot_fig1_throughput_vs_width(
    sweep_csv: Path,
    outdir: Path,
    *,
    l_meas: int = 1,
    l_ff: int = 1,
    policy: str = "asap",
) -> None:
    """Figure 1: Throughput vs Issue Width per algorithm (fixed L_meas, L_ff, policy)."""
    rows = _load_csv(sweep_csv)
    filtered = [
        r
        for r in _select_mainline_rows(rows)
        if int(r["l_meas"]) == l_meas
        and int(r["l_ff"]) == l_ff
        and r["policy"] == policy
    ]

    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in filtered:
        grouped[r["algorithm"]][int(r["issue_width"])].append(float(r["throughput"]))

    fig, ax = plt.subplots(figsize=(8, 5))
    for algo in sorted(grouped.keys()):
        ws = sorted(grouped[algo].keys())
        medians = []
        for w in ws:
            medians.append(_median(grouped[algo][w]))
        ax.plot(
            ws,
            medians,
            marker=ALGO_MARKERS.get(algo, "o"),
            color=ALGO_COLORS.get(algo, "gray"),
            label=algo,
            linewidth=2,
        )

    ax.set_xlabel("Issue Width (W)", fontsize=12)
    ax.set_ylabel("Throughput (nodes/cycle)", fontsize=12)
    ax.set_title(
        f"Throughput vs Issue Width — controlled coupled subset "
        f"(L_meas={l_meas}, L_ff={l_ff}, {policy})"
    )
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.legend()
    ax.grid(True, alpha=0.3)
    _save(fig, outdir, "fig1_throughput_vs_width")


def plot_fig2_stall_heatmap(
    sweep_csv: Path,
    outdir: Path,
    *,
    algorithm: str = "QFT",
    l_meas: int = 1,
    policy: str = "asap",
) -> None:
    """Figure 2: Stall Rate heatmap (W x L_ff) for a given algorithm."""
    rows = _load_csv(sweep_csv)
    filtered = [
        r
        for r in _select_mainline_rows(rows)
        if r["algorithm"] == algorithm
        and int(r["l_meas"]) == l_meas
        and r["policy"] == policy
    ]

    data: dict[tuple[int, int], list[float]] = defaultdict(list)
    ws_set: set[int] = set()
    lfs_set: set[int] = set()
    for r in filtered:
        w = int(r["issue_width"])
        lf = int(r["l_ff"])
        ws_set.add(w)
        lfs_set.add(lf)
        data[(w, lf)].append(float(r["stall_rate"]))

    ws = sorted(ws_set)
    lfs = sorted(lfs_set)

    import numpy as np

    grid = np.zeros((len(lfs), len(ws)))
    for i, lf in enumerate(lfs):
        for j, w in enumerate(ws):
            vals = data.get((w, lf), [0.0])
            grid[i, j] = _median(vals)

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(grid, aspect="auto", cmap="YlOrRd", origin="lower", vmin=0, vmax=1)
    ax.set_xticks(range(len(ws)))
    ax.set_xticklabels([str(w) for w in ws])
    ax.set_yticks(range(len(lfs)))
    ax.set_yticklabels([str(lf) for lf in lfs])
    ax.set_xlabel("Issue Width (W)")
    ax.set_ylabel("FF Latency (L_ff)")
    ax.set_title(
        f"Stall Rate — {algorithm} (controlled coupled subset, L_meas={l_meas}, {policy})"
    )

    for i in range(len(lfs)):
        for j in range(len(ws)):
            val = grid[i, j]
            color = "white" if val > 0.5 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=color, fontsize=9)

    fig.colorbar(im, ax=ax, label="Stall Rate")
    _save(fig, outdir, f"fig2_stall_heatmap_{algorithm}")


def plot_fig3_ilp_profile(
    sweep_csv: Path,
    outdir: Path,
    *,
    l_meas: int = 1,
    l_ff: int = 1,
    issue_width: int = 16,
    policy: str = "asap",
) -> None:
    """Figure 3: ILP Profile — static DAG parallelism per algorithm.

    Uses throughput at max issue-width as a proxy for available ILP.
    Shows throughput vs Q for the common coupled subset only.
    """
    rows = _load_csv(sweep_csv)
    filtered = [
        r
        for r in _select_mainline_rows(rows)
        if int(r["l_meas"]) == l_meas
        and int(r["l_ff"]) == l_ff
        and int(r["issue_width"]) == issue_width
        and r["policy"] == policy
    ]

    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in filtered:
        grouped[r["algorithm"]][int(r["logical_qubits"])].append(float(r["throughput"]))

    fig, ax = plt.subplots(figsize=(8, 5))
    for algo in sorted(grouped.keys()):
        qs = sorted(grouped[algo].keys())
        medians = [_median(grouped[algo][q]) for q in qs]
        ax.plot(
            qs,
            medians,
            marker=ALGO_MARKERS.get(algo, "o"),
            color=ALGO_COLORS.get(algo, "gray"),
            label=algo,
            linewidth=2,
        )

    ax.set_xlabel("Logical Qubits (Q)", fontsize=12)
    ax.set_ylabel(f"Throughput at W={issue_width} (nodes/cycle)", fontsize=12)
    ax.set_title(
        f"ILP Proxy at W={issue_width} — controlled coupled subset "
        f"(L_meas={l_meas}, L_ff={l_ff}, {policy})"
    )
    ax.legend()
    ax.grid(True, alpha=0.3)
    _save(fig, outdir, "fig3_ilp_profile")


def plot_fig4_policy_comparison(
    sweep_csv: Path,
    outdir: Path,
    *,
    l_meas: int = 1,
    l_ff: int = 2,
    issue_width: int = 4,
) -> None:
    """Figure 4: Policy comparison — throughput per algorithm across policies."""
    rows = _load_csv(sweep_csv)
    filtered = [
        r
        for r in _select_mainline_rows(rows)
        if int(r["l_meas"]) == l_meas
        and int(r["l_ff"]) == l_ff
        and int(r["issue_width"]) == issue_width
    ]

    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in filtered:
        grouped[r["algorithm"]][r["policy"]].append(float(r["throughput"]))

    algos = sorted(grouped.keys())
    policies = sorted({r["policy"] for r in filtered})

    import numpy as np

    x = np.arange(len(algos))
    width = 0.8 / len(policies)

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, pol in enumerate(policies):
        medians = []
        for algo in algos:
            medians.append(_median(grouped[algo].get(pol, [0.0])))
        ax.bar(x + i * width, medians, width, label=pol, alpha=0.85)

    ax.set_xlabel("Algorithm")
    ax.set_ylabel("Throughput (nodes/cycle)")
    ax.set_title(
        f"Policy Comparison — controlled coupled subset "
        f"(W={issue_width}, L_meas={l_meas}, L_ff={l_ff})"
    )
    ax.set_xticks(x + width * (len(policies) - 1) / 2)
    ax.set_xticklabels(algos)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    _save(fig, outdir, "fig4_policy_comparison")


def plot_fig5_feasibility(
    sweep_csv: Path,
    outdir: Path,
    *,
    tau_ph_us: float = 1.0,
) -> None:
    """Figure 5: Static FF budget context for the controlled coupled subset."""
    rows = _load_csv(sweep_csv)
    filtered = [
        r
        for r in _select_mainline_rows(rows)
        if int(r["issue_width"]) == 1
        and int(r["l_meas"]) == 1
        and int(r["l_ff"]) == 1
        and r["policy"] == "asap"
    ]

    raw_budget: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    shifted_budget: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in filtered:
        algo = r["algorithm"]
        q = int(r["logical_qubits"])
        d_raw = int(r["ff_chain_depth_raw"])
        raw_budget[algo][q].append((tau_ph_us * 1e3) / d_raw)
        shifted_raw = r.get("ff_chain_depth_shifted", "")
        if shifted_raw:
            d_shifted = int(shifted_raw)
            shifted_budget[algo][q].append((tau_ph_us * 1e3) / d_shifted)

    fig, ax = plt.subplots(figsize=(9, 5))
    for algo in sorted(raw_budget.keys()):
        qs = sorted(raw_budget[algo].keys())
        raw_vals = [_median(raw_budget[algo][q]) for q in qs]
        ax.plot(
            qs,
            raw_vals,
            marker=ALGO_MARKERS.get(algo, "o"),
            color=ALGO_COLORS.get(algo, "gray"),
            linestyle="-",
            linewidth=2,
            label=f"{algo} raw",
        )
        if shifted_budget[algo]:
            shifted_qs = sorted(shifted_budget[algo].keys())
            shifted_vals = [_median(shifted_budget[algo][q]) for q in shifted_qs]
            ax.plot(
                shifted_qs,
                shifted_vals,
                marker=ALGO_MARKERS.get(algo, "o"),
                color=ALGO_COLORS.get(algo, "gray"),
                linestyle="--",
                linewidth=2,
                label=f"{algo} shifted",
            )

    ax.axhline(250.0, color="#444444", linestyle=":", linewidth=1.5, label="OPX 250 ns")
    ax.axhline(185.0, color="#777777", linestyle=":", linewidth=1.5, label="XCOM 185 ns")
    ax.set_xlabel("Logical Qubits (Q)")
    ax.set_ylabel("Per-stage FF budget (ns)")
    ax.set_yscale("log")
    ax.set_title(f"Static FF Budget Context — controlled coupled subset (τ_ph={tau_ph_us} μs)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, ncol=2)
    _save(fig, outdir, "fig5_feasibility")


def plot_fig6_conservative_alignment(
    baseline_csv: Path,
    conservative_csv: Path,
    outdir: Path,
    *,
    l_meas: int = 1,
    l_ff: int = 2,
    policy: str = "asap",
) -> None:
    """Figure 6: baseline vs conservative throughput when ff_width matches W."""
    baseline_rows = [
        row
        for row in _select_mainline_rows(_load_csv(baseline_csv))
        if int(row["l_meas"]) == l_meas
        and int(row["l_ff"]) == l_ff
        and row["policy"] == policy
        and int(row["issue_width"]) in {1, 2, 4, 8}
    ]
    conservative_rows = [
        row
        for row in _select_conservative_rows(_load_csv(conservative_csv))
        if int(row["l_meas"]) == l_meas
        and int(row["l_ff"]) == l_ff
        and row["policy"] == policy
        and row.get("ff_width", "") == row["issue_width"]
        and int(row["issue_width"]) in {1, 2, 4, 8}
    ]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for ax, algo in zip(axes, ("QAOA", "QFT", "VQE")):
        base_group: dict[int, list[float]] = defaultdict(list)
        cons_group: dict[int, list[float]] = defaultdict(list)
        for row in baseline_rows:
            if row["algorithm"] == algo:
                base_group[int(row["issue_width"])].append(float(row["throughput"]))
        for row in conservative_rows:
            if row["algorithm"] == algo:
                cons_group[int(row["issue_width"])].append(float(row["throughput"]))

        widths = sorted(set(base_group) & set(cons_group))
        baseline_tp = [_median(base_group[w]) for w in widths]
        conservative_tp = [_median(cons_group[w]) for w in widths]

        ax.plot(
            widths,
            baseline_tp,
            marker=ALGO_MARKERS[algo],
            color=ALGO_COLORS[algo],
            linewidth=2,
            label="Baseline",
        )
        ax.plot(
            widths,
            conservative_tp,
            marker=ALGO_MARKERS[algo],
            color=ALGO_COLORS[algo],
            linewidth=2,
            linestyle="--",
            label="Conservative (ff_width = W)",
        )
        ax.set_title(algo)
        ax.set_xlabel("Issue Width (W)")
        ax.set_xscale("log", base=2)
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Throughput (nodes/cycle)")
    axes[0].legend(fontsize=8)
    fig.suptitle(
        f"Conservative Model Preserves Baseline Trend When ff_width = W "
        f"(L_meas={l_meas}, L_ff={l_ff}, {policy})"
    )
    fig.tight_layout()
    _save(fig, outdir, "fig6_conservative_alignment")


def plot_fig7_ff_underprovisioning(
    conservative_csv: Path,
    outdir: Path,
    *,
    l_meas: int = 1,
    l_ff: int = 2,
) -> None:
    """Figure 7: normalized throughput penalty when ff_width < W."""
    rows = [
        row
        for row in _select_conservative_rows(_load_csv(conservative_csv))
        if int(row["l_meas"]) == l_meas
        and int(row["l_ff"]) == l_ff
    ]

    panel_specs = [
        ("W=4, ASAP", 4, "asap"),
        ("W=8, GreedyCritical", 8, "greedy_critical"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)

    for ax, (title, issue_width, policy) in zip(axes, panel_specs):
        for algo in ("QAOA", "QFT", "VQE"):
            grouped: dict[int, list[float]] = defaultdict(list)
            for row in rows:
                if (
                    row["algorithm"] == algo
                    and int(row["issue_width"]) == issue_width
                    and row["policy"] == policy
                ):
                    grouped[int(row["ff_width"])].append(float(row["throughput"]))

            ff_widths = sorted(grouped)
            if not ff_widths or issue_width not in grouped:
                continue
            matched = _median(grouped[issue_width])
            ratios = [_median(grouped[w]) / matched for w in ff_widths]
            x_values = [w / issue_width for w in ff_widths]

            ax.plot(
                x_values,
                ratios,
                marker=ALGO_MARKERS[algo],
                color=ALGO_COLORS[algo],
                linewidth=2,
                label=algo,
            )

        ax.set_title(title)
        ax.set_xlabel("ff_width / W")
        ax.set_xscale("log", base=2)
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
        ax.set_xticks(sorted({0.125, 0.25, 0.5, 1.0}))
        ax.set_xticklabels(["1/8", "1/4", "1/2", "1"])
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Normalized Throughput\n(relative to ff_width = W)")
    axes[0].legend(fontsize=8)
    fig.suptitle(
        f"Underprovisioning FF Width Rapidly Degrades Throughput "
        f"(next_cycle, L_meas={l_meas}, L_ff={l_ff})"
    )
    fig.tight_layout()
    _save(fig, outdir, "fig7_ff_underprovisioning")


def plot_fig8_stage_width_comparison(
    ff_conservative_csv: Path,
    meas_conservative_csv: Path,
    outdir: Path,
    *,
    l_meas: int = 1,
    l_ff: int = 2,
) -> None:
    """Figure 8: compare FF-width vs measurement-width underprovisioning."""
    ff_rows = [
        row
        for row in _select_next_cycle_rows(_load_csv(ff_conservative_csv))
        if int(row["l_meas"]) == l_meas and int(row["l_ff"]) == l_ff
    ]
    meas_rows = [
        row
        for row in _select_next_cycle_rows(_load_csv(meas_conservative_csv))
        if int(row["l_meas"]) == l_meas and int(row["l_ff"]) == l_ff
    ]

    panel_specs = [
        ("W=4, ASAP", 4, "asap"),
        ("W=8, GreedyCritical", 8, "greedy_critical"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)

    for ax, (title, issue_width, policy) in zip(axes, panel_specs):
        for algo in ("QAOA", "QFT", "VQE"):
            ff_grouped: dict[int, list[float]] = defaultdict(list)
            meas_grouped: dict[int, list[float]] = defaultdict(list)

            for row in ff_rows:
                if (
                    row["algorithm"] == algo
                    and int(row["issue_width"]) == issue_width
                    and row["policy"] == policy
                ):
                    ff_grouped[int(row["ff_width"])].append(float(row["throughput"]))

            for row in meas_rows:
                if (
                    row["algorithm"] == algo
                    and int(row["issue_width"]) == issue_width
                    and row["policy"] == policy
                    and int(row["ff_width"]) == issue_width
                ):
                    meas_grouped[int(row["meas_width"])].append(float(row["throughput"]))

            if issue_width not in ff_grouped or issue_width not in meas_grouped:
                continue

            ff_base = _median(ff_grouped[issue_width])
            meas_base = _median(meas_grouped[issue_width])

            ff_widths = sorted(ff_grouped)
            meas_widths = sorted(meas_grouped)
            ff_ratios = [_median(ff_grouped[w]) / ff_base for w in ff_widths]
            meas_ratios = [_median(meas_grouped[w]) / meas_base for w in meas_widths]

            ax.plot(
                [w / issue_width for w in ff_widths],
                ff_ratios,
                marker=ALGO_MARKERS[algo],
                color=ALGO_COLORS[algo],
                linewidth=2,
                linestyle="-",
                label=f"{algo} (ff_width)",
            )
            ax.plot(
                [w / issue_width for w in meas_widths],
                meas_ratios,
                marker=ALGO_MARKERS[algo],
                color=ALGO_COLORS[algo],
                linewidth=2,
                linestyle="--",
                label=f"{algo} (meas_width)",
            )

        ax.set_title(title)
        ax.set_xlabel("stage width / W")
        ax.set_xscale("log", base=2)
        ticks = sorted({0.125, 0.25, 0.5, 1.0})
        ax.set_xticks(ticks)
        ax.set_xticklabels(["1/8", "1/4", "1/2", "1"])
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("Normalized Throughput")
    axes[0].legend(fontsize=7, ncol=2)
    fig.suptitle(
        f"Measurement- and FF-Width Underprovisioning Cause Similar Throughput Loss "
        f"(next_cycle, L_meas={l_meas}, L_ff={l_ff})"
    )
    fig.tight_layout()
    _save(fig, outdir, "fig8_stage_width_comparison")


def plot_fig9_shifted_throughput_comparison(
    comparison_csv: Path,
    outdir: Path,
) -> None:
    """Figure 9: raw vs shifted throughput on the controlled dynamic-comparison subset."""
    rows = _select_shifted_comparison_rows(_load_csv(comparison_csv))
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)

    for ax, algo in zip(axes, ("QAOA", "QFT", "VQE")):
        algo_rows = [row for row in rows if row["algorithm"] == algo]
        raw_grouped: dict[str, list[float]] = defaultdict(list)
        shifted_grouped: dict[str, list[float]] = defaultdict(list)
        for row in algo_rows:
            label = _pair_label(row)
            raw_grouped[label].append(float(row["throughput_raw_median"]))
            shifted_grouped[label].append(float(row["throughput_shifted_median"]))

        labels = sorted(raw_grouped)
        x = list(range(len(labels)))
        raw_vals = [_median(raw_grouped[label]) for label in labels]
        shifted_vals = [_median(shifted_grouped[label]) for label in labels]
        width = 0.36

        ax.bar(
            [pos - width / 2 for pos in x],
            raw_vals,
            width=width,
            color="#9aa4b2",
            label="raw",
        )
        ax.bar(
            [pos + width / 2 for pos in x],
            shifted_vals,
            width=width,
            color=ALGO_COLORS[algo],
            label="shifted",
        )
        ax.set_title(algo)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.grid(True, alpha=0.3, axis="y")

    axes[0].set_ylabel("Throughput (nodes/cycle)")
    axes[0].legend(fontsize=8)
    fig.suptitle(
        "Raw vs Shifted Throughput — next_cycle, width-matched controller subset"
    )
    fig.tight_layout()
    _save(fig, outdir, "fig9_shifted_throughput_comparison")


def plot_fig10_shifted_stall_comparison(
    comparison_csv: Path,
    outdir: Path,
) -> None:
    """Figure 10: raw vs shifted stall rate on the controlled dynamic-comparison subset."""
    rows = _select_shifted_comparison_rows(_load_csv(comparison_csv))
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)

    for ax, algo in zip(axes, ("QAOA", "QFT", "VQE")):
        algo_rows = [row for row in rows if row["algorithm"] == algo]
        raw_grouped: dict[str, list[float]] = defaultdict(list)
        shifted_grouped: dict[str, list[float]] = defaultdict(list)
        for row in algo_rows:
            label = _pair_label(row)
            raw_grouped[label].append(float(row["stall_rate_raw_median"]))
            shifted_grouped[label].append(float(row["stall_rate_shifted_median"]))

        labels = sorted(raw_grouped)
        x = list(range(len(labels)))
        raw_vals = [_median(raw_grouped[label]) for label in labels]
        shifted_vals = [_median(shifted_grouped[label]) for label in labels]
        width = 0.36

        ax.bar(
            [pos - width / 2 for pos in x],
            raw_vals,
            width=width,
            color="#c7cbd1",
            label="raw",
        )
        ax.bar(
            [pos + width / 2 for pos in x],
            shifted_vals,
            width=width,
            color=ALGO_COLORS[algo],
            label="shifted",
        )
        ax.set_title(algo)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.grid(True, alpha=0.3, axis="y")

    axes[0].set_ylabel("Stall Rate")
    axes[0].legend(fontsize=8)
    fig.suptitle(
        "Raw vs Shifted Stall Rate — next_cycle, width-matched controller subset"
    )
    fig.tight_layout()
    _save(fig, outdir, "fig10_shifted_stall_comparison")


def plot_fig11_depth_reduction_vs_throughput_gain(
    comparison_csv: Path,
    outdir: Path,
) -> None:
    """Figure 11: static depth reduction vs dynamic throughput gain."""
    rows = _select_shifted_comparison_rows(_load_csv(comparison_csv))
    fig, ax = plt.subplots(figsize=(8, 5))

    pair_markers = {
        ("4", "16"): "o",
        ("6", "36"): "s",
        ("8", "64"): "^",
    }
    for algo in ("QAOA", "QFT", "VQE"):
        algo_rows = [row for row in rows if row["algorithm"] == algo]
        for pair in COMMON_COUPLED_PAIRS:
            pair_rows = [
                row
                for row in algo_rows
                if (row["hardware_size"], row["logical_qubits"]) == pair
            ]
            if not pair_rows:
                continue
            ax.scatter(
                [float(row["depth_reduction_pct"]) for row in pair_rows],
                [float(row["throughput_gain_pct"]) for row in pair_rows],
                color=ALGO_COLORS[algo],
                marker=pair_markers[pair],
                s=60,
                alpha=0.85,
                label=f"{algo} H{pair[0]}Q{pair[1]}",
            )

    ax.axhline(0.0, color="#666666", linestyle=":", linewidth=1.2)
    ax.axvline(0.0, color="#666666", linestyle=":", linewidth=1.2)
    ax.set_xlabel("Static Depth Reduction (%)")
    ax.set_ylabel("Throughput Gain (%)")
    ax.set_title("Static Depth Reduction vs Dynamic Throughput Gain")
    ax.grid(True, alpha=0.3)

    handles, labels = ax.get_legend_handles_labels()
    dedup: dict[str, object] = {}
    for handle, label in zip(handles, labels):
        dedup.setdefault(label, handle)
    ax.legend(dedup.values(), dedup.keys(), fontsize=7, ncol=3)
    _save(fig, outdir, "fig11_depth_reduction_vs_throughput_gain")


def plot_all(
    sweep_csv: Path,
    outdir: Path,
    *,
    conservative_csv: Path | None = None,
    conservative_meas_csv: Path | None = None,
    comparison_csv: Path | None = None,
) -> None:
    """Generate all standard figures."""
    plot_fig1_throughput_vs_width(sweep_csv, outdir)
    plot_fig1_throughput_vs_width(sweep_csv, outdir, l_ff=2)

    for algo in ("QAOA", "QFT", "VQE"):
        plot_fig2_stall_heatmap(sweep_csv, outdir, algorithm=algo)

    plot_fig3_ilp_profile(sweep_csv, outdir)
    plot_fig4_policy_comparison(sweep_csv, outdir)
    plot_fig5_feasibility(sweep_csv, outdir)
    if conservative_csv is not None and conservative_csv.exists():
        plot_fig6_conservative_alignment(sweep_csv, conservative_csv, outdir)
        plot_fig7_ff_underprovisioning(conservative_csv, outdir)
        if conservative_meas_csv is not None and conservative_meas_csv.exists():
            plot_fig8_stage_width_comparison(conservative_csv, conservative_meas_csv, outdir)
    if comparison_csv is not None and comparison_csv.exists():
        plot_fig9_shifted_throughput_comparison(comparison_csv, outdir)
        plot_fig10_shifted_stall_comparison(comparison_csv, outdir)
        plot_fig11_depth_reduction_vs_throughput_gain(comparison_csv, outdir)
