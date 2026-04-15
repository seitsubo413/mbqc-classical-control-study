from __future__ import annotations

from mbqc_ff_evaluator.cli.aggregate import _aggregate_group
from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus, DependencyKind, ReferenceKind
from mbqc_ff_evaluator.domain.models import (
    DepthReference,
    ExperimentConfig,
    FFEdge,
    FFNode,
    OnePercArtifact,
)


def test_aggregate_group_uses_budget_medians_without_flooring() -> None:
    group = [
        OnePercArtifact(
            config=ExperimentConfig(
                algorithm=Algorithm.QAOA,
                hardware_size=4,
                logical_qubits=16,
                seed=0,
                refresh=True,
                refresh_bound=20,
            ),
            status=ArtifactStatus.SUCCESS,
            layer_index=1.0,
            required_lifetime_layers=30,
            max_measure_delay_layers=40,
            dgraph_num_nodes=2,
            dgraph_num_edges=1,
            ff_nodes=(FFNode(node_id=1, phase=None, node_type="Aux"),),
            ff_edges=(FFEdge(src=1, dst=2, dependency=DependencyKind.X),),
            ff_chain_depth_raw=10,
            ff_chain_depth_shifted=2,
            depth_reference=DepthReference(kind=ReferenceKind.INDEPENDENT_COMPILER, depth=6),
            elapsed_sec=0.1,
        ),
        OnePercArtifact(
            config=ExperimentConfig(
                algorithm=Algorithm.QAOA,
                hardware_size=4,
                logical_qubits=16,
                seed=1,
                refresh=True,
                refresh_bound=20,
            ),
            status=ArtifactStatus.SUCCESS,
            layer_index=1.0,
            required_lifetime_layers=31,
            max_measure_delay_layers=41,
            dgraph_num_nodes=2,
            dgraph_num_edges=1,
            ff_nodes=(FFNode(node_id=1, phase=None, node_type="Aux"),),
            ff_edges=(FFEdge(src=1, dst=2, dependency=DependencyKind.X),),
            ff_chain_depth_raw=10,
            ff_chain_depth_shifted=2,
            depth_reference=DepthReference(kind=ReferenceKind.INDEPENDENT_COMPILER, depth=8),
            elapsed_sec=0.1,
        ),
    ]

    row = _aggregate_group("QAOA", 4, 16, group, tau_ph_us=1.0)

    assert row.t_hold_ns_median is not None
    assert 32.7 < row.t_hold_ns_median < 32.9
    assert row.is_coupled is True
    assert row.depth_reference_kind == ReferenceKind.INDEPENDENT_COMPILER.value
    assert row.depth_reference_median == 7.0
