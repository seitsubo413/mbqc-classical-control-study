"""Shared fixtures for sweep experiments.

Usage:
    pytest -m bringup           # Quick bring-up (4 cases, ~20s)
    pytest -m pilot             # Pilot variance (10 cases, ~30s)
    pytest -m sweep_a           # Main Sweep A  (multi-algo × H × seeds)
    pytest -m sweep_b           # Sweep B: fixed Q, varying H
    pytest -m sweep_c           # Sweep C: fixed H, varying Q
    pytest -m pipeline          # Aggregate + plot from existing results
    pytest -m "not slow"        # Everything except large sweeps
"""

from __future__ import annotations

import pytest

from mbqc_ff_evaluator.adapters.json_repository import JsonArtifactRepository
from mbqc_ff_evaluator.adapters.oneadapt_backend import OneAdaptBackend
from mbqc_ff_evaluator.services.collect_artifacts import ArtifactCollectionService

from tests.helpers import RESULTS_RAW


@pytest.fixture(scope="session")
def oneadapt_backend() -> OneAdaptBackend:
    return OneAdaptBackend(verbose=False)


@pytest.fixture(scope="session")
def raw_repository() -> JsonArtifactRepository:
    return JsonArtifactRepository(RESULTS_RAW)


@pytest.fixture(scope="session")
def collection_service(
    oneadapt_backend: OneAdaptBackend,
    raw_repository: JsonArtifactRepository,
) -> ArtifactCollectionService:
    return ArtifactCollectionService(
        compiler_backend=oneadapt_backend,
        repository=raw_repository,
    )
