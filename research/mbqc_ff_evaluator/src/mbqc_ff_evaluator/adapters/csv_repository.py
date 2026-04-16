from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence

from mbqc_ff_evaluator.domain.enums import ConstraintKind
from mbqc_ff_evaluator.domain.models import OnePercArtifact

METRICS_COLUMNS = [
    "algorithm",
    "hardware_size",
    "logical_qubits",
    "seed",
    "status",
    "layer_index",
    "required_lifetime_layers",
    "max_measure_delay_layers",
    "dgraph_num_nodes",
    "dgraph_num_edges",
    "ff_chain_depth_raw",
    "ff_chain_depth_shifted",
    "shifted_unavailable_reason",
    "depth_reference_kind",
    "depth_reference_depth",
    "elapsed_sec",
]


@dataclass(frozen=True)
class BudgetSummaryRow:
    algorithm: str
    hardware_size: int
    logical_qubits: int
    tau_ph_us: float
    n_seeds: int
    is_coupled: bool
    depth_raw_median: float
    depth_raw_q1: float
    depth_raw_q3: float
    depth_raw_mean: float
    depth_shifted_median: float | None
    depth_shifted_q1: float | None
    depth_shifted_q3: float | None
    depth_reference_kind: str | None
    depth_reference_median: float | None
    depth_reference_q1: float | None
    depth_reference_q3: float | None
    t_ff_shifted_ns_median: float | None
    t_ff_shifted_ns_q1: float | None
    t_ff_shifted_ns_q3: float | None
    hold_median: float | None
    hold_q1: float | None
    hold_q3: float | None
    meas_median: float | None
    meas_q1: float | None
    meas_q3: float | None
    t_ff_cond_ns_median: float
    t_ff_cond_ns_q1: float
    t_ff_cond_ns_q3: float
    t_hold_ns_median: float | None
    t_hold_ns_q1: float | None
    t_hold_ns_q3: float | None
    t_meas_ns_median: float | None
    t_meas_ns_q1: float | None
    t_meas_ns_q3: float | None
    t_cons_ns_median: float | None
    t_cons_ns_q1: float | None
    t_cons_ns_q3: float | None
    dominant_constraint: ConstraintKind | None


class CsvSummaryRepository:
    """CSV persistence for per-seed metrics and aggregated budget summaries."""

    def __init__(self, summary_directory: Path) -> None:
        self._summary_directory = summary_directory
        self._summary_directory.mkdir(parents=True, exist_ok=True)

    def write_metrics(self, artifacts: Sequence[OnePercArtifact]) -> Path:
        path = self._summary_directory / "metrics.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=METRICS_COLUMNS)
            writer.writeheader()
            for art in artifacts:
                writer.writerow(
                    {
                        "algorithm": art.config.algorithm.value,
                        "hardware_size": art.config.hardware_size,
                        "logical_qubits": art.config.logical_qubits,
                        "seed": art.config.seed,
                        "status": art.status.value,
                        "layer_index": art.layer_index,
                        "required_lifetime_layers": art.required_lifetime_layers,
                        "max_measure_delay_layers": art.max_measure_delay_layers,
                        "dgraph_num_nodes": art.dgraph_num_nodes,
                        "dgraph_num_edges": art.dgraph_num_edges,
                        "ff_chain_depth_raw": art.ff_chain_depth_raw,
                        "ff_chain_depth_shifted": art.ff_chain_depth_shifted,
                        "shifted_unavailable_reason": art.shifted_unavailable_reason,
                        "depth_reference_kind": (
                            None if art.depth_reference is None else art.depth_reference.kind.value
                        ),
                        "depth_reference_depth": (
                            None if art.depth_reference is None else art.depth_reference.depth
                        ),
                        "elapsed_sec": f"{art.elapsed_sec:.3f}",
                    }
                )
        return path

    def write_budgets(self, rows: Sequence[BudgetSummaryRow]) -> Path:
        path = self._summary_directory / "budgets.csv"
        if not rows:
            return path
        header = list(asdict(rows[0]).keys())
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=header)
            writer.writeheader()
            for row in rows:
                writer.writerow(_serialize_csv_dict(asdict(row)))
        return path


def _serialize_csv_dict(payload: dict[str, object]) -> dict[str, object]:
    serialized: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, Enum):
            serialized[key] = value.value
        else:
            serialized[key] = value
    return serialized
