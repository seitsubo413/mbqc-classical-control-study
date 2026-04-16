"""Shared test helpers for sweep experiments."""

from __future__ import annotations

from pathlib import Path

from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus
from mbqc_ff_evaluator.domain.models import ExperimentConfig, OnePercArtifact
from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService

RESULTS_RAW = Path(__file__).resolve().parents[1] / "results" / "raw"
RESULTS_SUMMARY = Path(__file__).resolve().parents[1] / "results" / "summary"
RESULTS_FIGURES = Path(__file__).resolve().parents[1] / "results" / "figures"


def run_single_experiment(
    service: ArtifactCollectionService,
    algorithm: str,
    hardware_size: int,
    logical_qubits: int,
    seed: int,
    refresh: bool = True,
    refresh_bound: int = 20,
) -> OnePercArtifact:
    config = ExperimentConfig(
        algorithm=Algorithm(algorithm),
        hardware_size=hardware_size,
        logical_qubits=logical_qubits,
        seed=seed,
        refresh=refresh,
        refresh_bound=refresh_bound,
    )
    record = service.collect(config)
    return record.artifact


def assert_artifact_valid(artifact: OnePercArtifact) -> None:
    assert artifact.status in (ArtifactStatus.SUCCESS, ArtifactStatus.TIMEOUT_GUARD)
    assert artifact.ff_chain_depth_raw >= 0
    assert artifact.dgraph_num_nodes > 0
    assert artifact.dgraph_num_edges >= 0
    assert artifact.elapsed_sec > 0
    if artifact.shifted_dependency_graph is not None:
        assert artifact.ff_chain_depth_shifted == artifact.shifted_dependency_graph.chain_depth
        assert len(artifact.shifted_dependency_graph.nodes) > 0

    if artifact.status == ArtifactStatus.SUCCESS:
        assert artifact.required_lifetime_layers is not None
        assert artifact.required_lifetime_layers > 0
        assert artifact.max_measure_delay_layers is not None
        assert artifact.max_measure_delay_layers > 0
        assert artifact.ff_chain_depth_raw > 0
