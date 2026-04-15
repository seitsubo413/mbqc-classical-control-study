from __future__ import annotations

from mbqc_ff_evaluator.analysis.outliers import analyze_measurement_delay_groups
from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus
from mbqc_ff_evaluator.domain.models import ExperimentConfig, OnePercArtifact


def _artifact(seed: int, meas: int) -> OnePercArtifact:
    return OnePercArtifact(
        config=ExperimentConfig(
            algorithm=Algorithm.QAOA,
            hardware_size=8,
            logical_qubits=64,
            seed=seed,
            refresh=True,
            refresh_bound=20,
        ),
        status=ArtifactStatus.SUCCESS,
        layer_index=1.0,
        required_lifetime_layers=40,
        max_measure_delay_layers=meas,
        dgraph_num_nodes=2,
        dgraph_num_edges=1,
        ff_nodes=(),
        ff_edges=(),
        ff_chain_depth_raw=140,
        ff_chain_depth_shifted=2,
        depth_reference=None,
        elapsed_sec=0.1,
    )


def test_analyze_measurement_delay_groups_flags_seed_sensitive_case() -> None:
    group_rows, outlier_rows = analyze_measurement_delay_groups(
        [_artifact(0, 35), _artifact(1, 38), _artifact(2, 40), _artifact(3, 1189)]
    )

    assert len(group_rows) == 1
    assert group_rows[0].outlier_count == 1
    assert group_rows[0].regime_hint in {"seed_sensitive", "mixed"}
    assert len(outlier_rows) == 1
    assert outlier_rows[0].seed == 3
