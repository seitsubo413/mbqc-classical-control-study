"""Persist simulation results to CSV."""
from __future__ import annotations

import csv
from pathlib import Path

from mbqc_pipeline_sim.domain.models import SimResult


_FIELDNAMES = [
    "dag_label",
    "dag_variant",
    "algorithm",
    "hardware_size",
    "logical_qubits",
    "dag_seed",
    "ff_chain_depth",
    "ff_chain_depth_raw",
    "ff_chain_depth_shifted",
    "policy",
    "release_mode",
    "issue_width",
    "l_meas",
    "l_ff",
    "meas_width",
    "ff_width",
    "total_nodes",
    "total_cycles",
    "throughput",
    "stall_cycles",
    "stall_rate",
    "utilization",
]


def write_results(results: list[SimResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "dag_label": r.dag_label,
                    "dag_variant": r.dag_variant.value,
                    "algorithm": r.algorithm,
                    "hardware_size": r.hardware_size,
                    "logical_qubits": r.logical_qubits,
                    "dag_seed": r.dag_seed,
                    "ff_chain_depth": r.ff_chain_depth,
                    "ff_chain_depth_raw": r.ff_chain_depth_raw,
                    "ff_chain_depth_shifted": r.ff_chain_depth_shifted
                    if r.ff_chain_depth_shifted is not None
                    else "",
                    "policy": r.config.policy.value,
                    "release_mode": r.config.release_mode.value,
                    "issue_width": r.config.issue_width,
                    "l_meas": r.config.l_meas,
                    "l_ff": r.config.l_ff,
                    "meas_width": r.config.meas_width if r.config.meas_width is not None else "",
                    "ff_width": r.config.ff_width if r.config.ff_width is not None else "",
                    "total_nodes": r.total_nodes,
                    "total_cycles": r.total_cycles,
                    "throughput": round(r.throughput, 6),
                    "stall_cycles": r.stall_cycles,
                    "stall_rate": round(r.stall_rate, 6),
                    "utilization": round(r.utilization, 6),
                }
            )
