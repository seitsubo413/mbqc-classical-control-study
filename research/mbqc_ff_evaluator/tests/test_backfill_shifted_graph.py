from __future__ import annotations

import json
from pathlib import Path

from mbqc_ff_evaluator.cli import backfill_shifted_graph as cli_module
from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus, DependencyKind
from mbqc_ff_evaluator.domain.models import (
    DependencyGraphSnapshot,
    ExperimentConfig,
    FFEdge,
    FFNode,
    OnePercArtifact,
)


class FakeBackend:
    def __init__(self, oneadapt_root: Path | None = None) -> None:
        self.oneadapt_root = oneadapt_root

    def collect_dependency_snapshots(
        self,
        config: ExperimentConfig,
    ) -> tuple[DependencyGraphSnapshot, DependencyGraphSnapshot | None]:
        raw_snapshot = DependencyGraphSnapshot(
            nodes=(FFNode(node_id=1, phase=None, node_type="M"),),
            edges=(FFEdge(src=1, dst=2, dependency=DependencyKind.X),),
            chain_depth=4,
        )
        shifted_snapshot = DependencyGraphSnapshot(
            nodes=(FFNode(node_id=1, phase=None, node_type="M"),),
            edges=(),
            chain_depth=2,
        )
        return raw_snapshot, shifted_snapshot


def test_backfill_shifted_graph_updates_existing_artifact(tmp_path: Path, monkeypatch) -> None:
    artifact = OnePercArtifact(
        config=ExperimentConfig(
            algorithm=Algorithm.QAOA,
            hardware_size=4,
            logical_qubits=16,
            seed=0,
            refresh=True,
            refresh_bound=20,
        ),
        status=ArtifactStatus.SUCCESS,
        layer_index=10.0,
        required_lifetime_layers=3,
        max_measure_delay_layers=4,
        dgraph_num_nodes=2,
        dgraph_num_edges=1,
        ff_nodes=(FFNode(node_id=1, phase=None, node_type="M"),),
        ff_edges=(FFEdge(src=1, dst=2, dependency=DependencyKind.X),),
        ff_chain_depth_raw=4,
        ff_chain_depth_shifted=None,
        depth_reference=None,
        elapsed_sec=0.1,
        shifted_dependency_graph=None,
    )

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    path = raw_dir / "QAOA_H4_Q16_seed0.json"
    path.write_text(json.dumps(_artifact_payload(artifact)), encoding="utf-8")

    monkeypatch.setattr(cli_module, "OneAdaptBackend", FakeBackend)

    exit_code = cli_module.main(["--raw-dir", str(raw_dir)])
    assert exit_code == 0

    updated_payload = json.loads(path.read_text(encoding="utf-8"))
    assert updated_payload["ff_chain_depth_shifted"] == 2
    assert updated_payload["shifted_dependency_graph"]["chain_depth"] == 2


def _artifact_payload(artifact: OnePercArtifact) -> dict[str, object]:
    return {
        "config": {
            "algorithm": artifact.config.algorithm.value,
            "hardware_size": artifact.config.hardware_size,
            "logical_qubits": artifact.config.logical_qubits,
            "seed": artifact.config.seed,
            "refresh": artifact.config.refresh,
            "refresh_bound": artifact.config.refresh_bound,
        },
        "status": artifact.status.value,
        "layer_index": artifact.layer_index,
        "required_lifetime_layers": artifact.required_lifetime_layers,
        "max_measure_delay_layers": artifact.max_measure_delay_layers,
        "dgraph_num_nodes": artifact.dgraph_num_nodes,
        "dgraph_num_edges": artifact.dgraph_num_edges,
        "ff_nodes": [
            {"node_id": node.node_id, "phase": node.phase, "node_type": node.node_type}
            for node in artifact.ff_nodes
        ],
        "ff_edges": [
            {"src": edge.src, "dst": edge.dst, "dependency": edge.dependency.value}
            for edge in artifact.ff_edges
        ],
        "ff_chain_depth_raw": artifact.ff_chain_depth_raw,
        "ff_chain_depth_shifted": artifact.ff_chain_depth_shifted,
        "depth_reference": None,
        "elapsed_sec": artifact.elapsed_sec,
        "shifted_dependency_graph": None,
    }
