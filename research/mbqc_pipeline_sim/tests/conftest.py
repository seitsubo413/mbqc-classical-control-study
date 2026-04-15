from pathlib import Path

import pytest

FF_EVAL_RAW = (
    Path(__file__).resolve().parents[2]
    / "mbqc_ff_evaluator"
    / "results"
    / "raw"
)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


@pytest.fixture
def small_artifact_path() -> Path:
    """QAOA H=4, Q=16, seed=0 — smallest DAG."""
    p = FF_EVAL_RAW / "QAOA_H4_Q16_seed0.json"
    if not p.exists():
        pytest.skip(f"Artifact not found: {p}")
    return p


@pytest.fixture
def qft_artifact_path() -> Path:
    """QFT H=4, Q=16, seed=0 — deeper FF chain."""
    p = FF_EVAL_RAW / "QFT_H4_Q16_seed0.json"
    if not p.exists():
        pytest.skip(f"Artifact not found: {p}")
    return p
