from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.adapters.oneadapt_backend import OneAdaptBackend
from mbqc_ff_evaluator.domain.enums import Algorithm
from mbqc_ff_evaluator.domain.models import ExperimentConfig, OnePercArtifact
from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService
from mbqc_ff_evaluator.services.compute_budgets import (
    compute_conservative_budget,
    compute_dependency_budget,
    compute_layer_budget,
    convert_latency_budget_to_clock,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a smoke experiment for MBQC FF evaluator")
    parser.add_argument(
        "--algorithm",
        required=True,
        choices=[algorithm.value for algorithm in Algorithm],
    )
    parser.add_argument("--hardware-size", type=int, required=True)
    parser.add_argument("--logical-qubits", type=int, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--refresh-bound", type=int, default=20)
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--photon-lifetime-us", type=float, default=1.0)
    parser.add_argument("--cycles-per-stage", type=int, default=1)
    parser.add_argument("--oneadapt-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--verbose-oneadapt", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = ExperimentConfig(
        algorithm=Algorithm(args.algorithm),
        hardware_size=args.hardware_size,
        logical_qubits=args.logical_qubits,
        seed=args.seed,
        refresh=not args.no_refresh,
        refresh_bound=args.refresh_bound,
    )
    backend = OneAdaptBackend(
        oneadapt_root=args.oneadapt_root,
        verbose=args.verbose_oneadapt,
    )
    repository = JsonArtifactRepository(args.output_dir or _default_output_dir())
    service = ArtifactCollectionService(
        compiler_backend=backend,
        repository=repository,
    )
    record = service.collect(config)
    summary = _build_summary_payload(
        artifact=record.artifact,
        artifact_path=record.artifact_path,
        photon_lifetime_us=args.photon_lifetime_us,
        cycles_per_stage=args.cycles_per_stage,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def _default_output_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "results" / "raw"


def _build_summary_payload(
    artifact: OnePercArtifact,
    artifact_path: Path,
    photon_lifetime_us: float,
    cycles_per_stage: int,
) -> dict[str, Any]:
    dependency_budget = compute_dependency_budget(
        dependency_depth=artifact.ff_chain_depth_raw,
        photon_lifetime_us=photon_lifetime_us,
    )
    hold_budget = (
        None
        if artifact.required_lifetime_layers is None
        else compute_layer_budget(
            layer_metric=artifact.required_lifetime_layers,
            photon_lifetime_us=photon_lifetime_us,
        )
    )
    meas_budget = (
        None
        if artifact.max_measure_delay_layers is None
        else compute_layer_budget(
            layer_metric=artifact.max_measure_delay_layers,
            photon_lifetime_us=photon_lifetime_us,
        )
    )
    conservative_budget = (
        None
        if hold_budget is None or meas_budget is None
        else compute_conservative_budget(
            dependency_budget=dependency_budget,
            hold_budget=hold_budget,
            meas_budget=meas_budget,
        )
    )
    return {
        "artifact_path": str(artifact_path),
        "status": artifact.status.value,
        "config": {
            "algorithm": artifact.config.algorithm.value,
            "hardware_size": artifact.config.hardware_size,
            "logical_qubits": artifact.config.logical_qubits,
            "seed": artifact.config.seed,
            "refresh": artifact.config.refresh,
            "refresh_bound": artifact.config.refresh_bound,
        },
        "artifact": {
            "layer_index": artifact.layer_index,
            "required_lifetime_layers": artifact.required_lifetime_layers,
            "max_measure_delay_layers": artifact.max_measure_delay_layers,
            "dgraph_num_nodes": artifact.dgraph_num_nodes,
            "dgraph_num_edges": artifact.dgraph_num_edges,
            "ff_chain_depth_raw": artifact.ff_chain_depth_raw,
            "ff_chain_depth_shifted": artifact.ff_chain_depth_shifted,
            "elapsed_sec": artifact.elapsed_sec,
        },
        "budgets": {
            "dependency": {
                "t_ff_cond_ns": dependency_budget.t_ff_cond_ns,
                "critical_clock_mhz": convert_latency_budget_to_clock(
                    latency_ns=dependency_budget.t_ff_cond_ns,
                    cycles_per_stage=cycles_per_stage,
                ),
            },
            "hold": None
            if hold_budget is None
            else {
                "per_layer_budget_ns": hold_budget.per_layer_budget_ns,
                "critical_clock_mhz": convert_latency_budget_to_clock(
                    latency_ns=hold_budget.per_layer_budget_ns,
                    cycles_per_stage=cycles_per_stage,
                ),
            },
            "measurement": None
            if meas_budget is None
            else {
                "per_layer_budget_ns": meas_budget.per_layer_budget_ns,
                "critical_clock_mhz": convert_latency_budget_to_clock(
                    latency_ns=meas_budget.per_layer_budget_ns,
                    cycles_per_stage=cycles_per_stage,
                ),
            },
            "conservative": None
            if conservative_budget is None
            else {
                "t_cons_ns": conservative_budget.t_cons_ns,
                "critical_clock_mhz": convert_latency_budget_to_clock(
                    latency_ns=conservative_budget.t_cons_ns,
                    cycles_per_stage=cycles_per_stage,
                ),
            },
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
