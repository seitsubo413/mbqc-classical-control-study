"""Additional pilot variance: QFT and VQE × H=4 × seeds 0-4.

Lighter pilot for QFT/VQE since H=6 may be too heavy for QFT.

Run with:
    pytest tests/test_sweep_pilot_extra.py -v -s
"""

from __future__ import annotations

import pytest

from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService

from tests.helpers import assert_artifact_valid, run_single_experiment

SEEDS_5 = list(range(5))


@pytest.mark.pilot
@pytest.mark.parametrize("seed", SEEDS_5, ids=[f"QFT_H4_Q16_s{s}" for s in SEEDS_5])
def test_pilot_qft_h4(
    collection_service: ArtifactCollectionService,
    seed: int,
) -> None:
    artifact = run_single_experiment(
        collection_service, "QFT", hardware_size=4, logical_qubits=16, seed=seed
    )
    assert_artifact_valid(artifact)
    print(
        f"\n  QFT H=4 Q=16 seed={seed}: "
        f"depth_raw={artifact.ff_chain_depth_raw} "
        f"depth_shifted={artifact.ff_chain_depth_shifted} "
        f"L_hold={artifact.required_lifetime_layers} "
        f"L_meas={artifact.max_measure_delay_layers} "
        f"elapsed={artifact.elapsed_sec:.1f}s"
    )


@pytest.mark.pilot
@pytest.mark.parametrize("seed", SEEDS_5, ids=[f"VQE_H4_Q16_s{s}" for s in SEEDS_5])
def test_pilot_vqe_h4(
    collection_service: ArtifactCollectionService,
    seed: int,
) -> None:
    artifact = run_single_experiment(
        collection_service, "VQE", hardware_size=4, logical_qubits=16, seed=seed
    )
    assert_artifact_valid(artifact)
    print(
        f"\n  VQE H=4 Q=16 seed={seed}: "
        f"depth_raw={artifact.ff_chain_depth_raw} "
        f"depth_shifted={artifact.ff_chain_depth_shifted} "
        f"L_hold={artifact.required_lifetime_layers} "
        f"L_meas={artifact.max_measure_delay_layers} "
        f"elapsed={artifact.elapsed_sec:.1f}s"
    )


@pytest.mark.pilot
@pytest.mark.parametrize("seed", SEEDS_5, ids=[f"VQE_H6_Q36_s{s}" for s in SEEDS_5])
def test_pilot_vqe_h6(
    collection_service: ArtifactCollectionService,
    seed: int,
) -> None:
    artifact = run_single_experiment(
        collection_service, "VQE", hardware_size=6, logical_qubits=36, seed=seed
    )
    assert_artifact_valid(artifact)
    print(
        f"\n  VQE H=6 Q=36 seed={seed}: "
        f"depth_raw={artifact.ff_chain_depth_raw} "
        f"depth_shifted={artifact.ff_chain_depth_shifted} "
        f"L_hold={artifact.required_lifetime_layers} "
        f"L_meas={artifact.max_measure_delay_layers} "
        f"elapsed={artifact.elapsed_sec:.1f}s"
    )
