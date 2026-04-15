"""Main sweep experiments (Sweep A / B / C).

Sweep A: Q = H^2 (coupled baseline)
Sweep B: fixed Q, varying H
Sweep C: fixed H, varying Q

Run with:
    pytest tests/test_sweep_main.py -v                     # all sweeps
    pytest -m sweep_a -v                                   # Sweep A only
    pytest -m sweep_b -v                                   # Sweep B only
    pytest -m sweep_c -v                                   # Sweep C only
    pytest tests/test_sweep_main.py -k "QAOA" -v           # QAOA only
    pytest tests/test_sweep_main.py -k "H8" -v             # H=8 only
"""

from __future__ import annotations

import pytest

from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService

from tests.helpers import assert_artifact_valid, run_single_experiment

ALGORITHMS = ["QAOA", "QFT", "VQE"]
SEEDS = [0, 1, 2, 3, 4]

# --- Sweep A: Q = H^2 ---
SWEEP_A_H_VALUES = [4, 6, 8, 10]
SWEEP_A_CASES = [
    (algo, h, h * h, seed)
    for algo in ALGORITHMS
    for h in SWEEP_A_H_VALUES
    for seed in SEEDS
]

# --- Sweep B: fixed Q, varying H ---
SWEEP_B_CASES_RAW = [
    ("QAOA", 6, 36),
    ("QAOA", 8, 36),
    ("QAOA", 10, 36),
    ("QAOA", 8, 64),
    ("QAOA", 10, 64),
    ("QAOA", 12, 64),
    ("QFT", 6, 36),
    ("QFT", 8, 36),
    ("QFT", 10, 36),
]
SWEEP_B_CASES = [
    (algo, h, q, seed) for algo, h, q in SWEEP_B_CASES_RAW for seed in SEEDS
]

# --- Sweep C: fixed H, varying Q ---
SWEEP_C_CASES_RAW = [
    ("QAOA", 8, 16),
    ("QAOA", 8, 36),
    ("QAOA", 8, 64),
    ("QAOA", 10, 36),
    ("QAOA", 10, 64),
    ("QAOA", 10, 100),
    ("QFT", 8, 16),
    ("QFT", 8, 36),
    ("QFT", 8, 64),
]
SWEEP_C_CASES = [
    (algo, h, q, seed) for algo, h, q in SWEEP_C_CASES_RAW for seed in SEEDS
]


def _case_id(algo: str, h: int, q: int, s: int) -> str:
    return f"{algo}_H{h}_Q{q}_s{s}"


@pytest.mark.sweep_a
@pytest.mark.slow
@pytest.mark.parametrize(
    "algorithm, hardware_size, logical_qubits, seed",
    SWEEP_A_CASES,
    ids=[_case_id(a, h, q, s) for a, h, q, s in SWEEP_A_CASES],
)
def test_sweep_a(
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
        f"\n  [A] {algorithm} H={hardware_size} Q={logical_qubits} seed={seed}: "
        f"depth_raw={artifact.ff_chain_depth_raw} "
        f"L_hold={artifact.required_lifetime_layers} "
        f"elapsed={artifact.elapsed_sec:.1f}s"
    )


@pytest.mark.sweep_b
@pytest.mark.slow
@pytest.mark.parametrize(
    "algorithm, hardware_size, logical_qubits, seed",
    SWEEP_B_CASES,
    ids=[_case_id(a, h, q, s) for a, h, q, s in SWEEP_B_CASES],
)
def test_sweep_b(
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
        f"\n  [B] {algorithm} H={hardware_size} Q={logical_qubits} seed={seed}: "
        f"depth_raw={artifact.ff_chain_depth_raw} "
        f"L_hold={artifact.required_lifetime_layers} "
        f"elapsed={artifact.elapsed_sec:.1f}s"
    )


@pytest.mark.sweep_c
@pytest.mark.slow
@pytest.mark.parametrize(
    "algorithm, hardware_size, logical_qubits, seed",
    SWEEP_C_CASES,
    ids=[_case_id(a, h, q, s) for a, h, q, s in SWEEP_C_CASES],
)
def test_sweep_c(
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
        f"\n  [C] {algorithm} H={hardware_size} Q={logical_qubits} seed={seed}: "
        f"depth_raw={artifact.ff_chain_depth_raw} "
        f"L_hold={artifact.required_lifetime_layers} "
        f"elapsed={artifact.elapsed_sec:.1f}s"
    )
