"""Bring-up experiments: QAOA/QFT × H=4,6 × seed=0.

Run with:
    pytest tests/test_sweep_bringup.py -v
    pytest -m bringup -v
"""

from __future__ import annotations

import pytest

from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService

from tests.helpers import assert_artifact_valid, run_single_experiment

BRINGUP_CASES = [
    ("QAOA", 4, 16, 0),
    ("QAOA", 6, 36, 0),
    ("QFT", 4, 16, 0),
    ("QFT", 6, 36, 0),
]


@pytest.mark.bringup
@pytest.mark.parametrize(
    "algorithm, hardware_size, logical_qubits, seed",
    BRINGUP_CASES,
    ids=[f"{a}_H{h}_Q{q}_s{s}" for a, h, q, s in BRINGUP_CASES],
)
def test_bringup(
    collection_service: ArtifactCollectionService,
    algorithm: str,
    hardware_size: int,
    logical_qubits: int,
    seed: int,
) -> None:
    artifact = run_single_experiment(
        collection_service, algorithm, hardware_size, logical_qubits, seed
    )
    assert_artifact_valid(artifact)

    print(
        f"\n  {algorithm} H={hardware_size} Q={logical_qubits} seed={seed}: "
        f"status={artifact.status.value} "
        f"depth_raw={artifact.ff_chain_depth_raw} "
        f"depth_shifted={artifact.ff_chain_depth_shifted} "
        f"L_hold={artifact.required_lifetime_layers} "
        f"L_meas={artifact.max_measure_delay_layers} "
        f"elapsed={artifact.elapsed_sec:.1f}s"
    )
