from __future__ import annotations

import pytest

from mbqc_ff_evaluator.domain.enums import DependencyKind
from mbqc_ff_evaluator.domain.errors import DependencyGraphError
from mbqc_ff_evaluator.domain.models import FFEdge
from mbqc_ff_evaluator.services.compute_metrics import (
    compute_ff_chain_depth_raw,
    compute_ff_chain_depth_shifted,
    validate_dag,
)


def test_compute_ff_chain_depth_raw_for_chain() -> None:
    edges = (
        FFEdge(src=1, dst=2, dependency=DependencyKind.X),
        FFEdge(src=2, dst=3, dependency=DependencyKind.Z),
    )
    assert compute_ff_chain_depth_raw((1, 2, 3), edges) == 2


def test_compute_ff_chain_depth_shifted_for_diamond() -> None:
    edges = (
        FFEdge(src=1, dst=2, dependency=DependencyKind.X),
        FFEdge(src=1, dst=3, dependency=DependencyKind.X),
        FFEdge(src=2, dst=4, dependency=DependencyKind.Z),
        FFEdge(src=3, dst=4, dependency=DependencyKind.Z),
    )
    assert compute_ff_chain_depth_shifted((1, 2, 3, 4), edges) == 2


def test_validate_dag_rejects_cycle() -> None:
    edges = (
        FFEdge(src=1, dst=2, dependency=DependencyKind.X),
        FFEdge(src=2, dst=3, dependency=DependencyKind.X),
        FFEdge(src=3, dst=1, dependency=DependencyKind.Z),
    )
    with pytest.raises(DependencyGraphError):
        validate_dag((1, 2, 3), edges)
