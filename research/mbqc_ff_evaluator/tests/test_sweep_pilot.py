"""Pilot variance experiment: QAOA × H=6 × seeds 0-9.

Checks seed variance before committing to full sweep.

Run with:
    pytest tests/test_sweep_pilot.py -v
    pytest -m pilot -v
"""

from __future__ import annotations

import pytest

from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService

from tests.helpers import assert_artifact_valid, run_single_experiment

PILOT_SEEDS = list(range(10))


@pytest.mark.pilot
@pytest.mark.parametrize("seed", PILOT_SEEDS, ids=[f"QAOA_H6_Q36_s{s}" for s in PILOT_SEEDS])
def test_pilot_qaoa_h6(
    collection_service: ArtifactCollectionService,
    seed: int,
) -> None:
    artifact = run_single_experiment(
        collection_service, "QAOA", hardware_size=6, logical_qubits=36, seed=seed
    )
    assert_artifact_valid(artifact)

    print(
        f"\n  QAOA H=6 Q=36 seed={seed}: "
        f"depth_raw={artifact.ff_chain_depth_raw} "
        f"depth_shifted={artifact.ff_chain_depth_shifted} "
        f"L_hold={artifact.required_lifetime_layers} "
        f"L_meas={artifact.max_measure_delay_layers} "
        f"elapsed={artifact.elapsed_sec:.1f}s"
    )
