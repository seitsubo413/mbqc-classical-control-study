from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from mbqc_ff_evaluator.domain.enums import Algorithm, ArtifactStatus, DependencyKind, ReferenceKind
from mbqc_ff_evaluator.domain.models import (
    ArtifactRecord,
    DepthReference,
    ExperimentConfig,
    FFEdge,
    FFNode,
    OnePercArtifact,
)
from mbqc_ff_evaluator.ports.repository import ArtifactRepository


class JsonArtifactRepository(ArtifactRepository):
    """Persist artifacts as JSON files."""

    def __init__(self, raw_directory: Path) -> None:
        self._raw_directory = raw_directory
        self._raw_directory.mkdir(parents=True, exist_ok=True)

    def save_artifact(self, artifact: OnePercArtifact) -> ArtifactRecord:
        filename = (
            f"{artifact.config.algorithm.value}_"
            f"H{artifact.config.hardware_size}_"
            f"Q{artifact.config.logical_qubits}_"
            f"seed{artifact.config.seed}.json"
        )
        path = self._raw_directory / filename
        payload = asdict(artifact)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return ArtifactRecord(artifact_path=path, artifact=artifact)

    def load_artifacts(self) -> Sequence[OnePercArtifact]:
        return tuple(
            self._deserialize_artifact(
                json.loads(path.read_text(encoding="utf-8")),
            )
            for path in sorted(self._raw_directory.glob("*.json"))
        )

    def _deserialize_artifact(self, payload: dict[str, Any]) -> OnePercArtifact:
        config_payload = payload["config"]
        depth_reference_payload = payload.get("depth_reference")
        return OnePercArtifact(
            config=ExperimentConfig(
                algorithm=Algorithm(config_payload["algorithm"]),
                hardware_size=int(config_payload["hardware_size"]),
                logical_qubits=int(config_payload["logical_qubits"]),
                seed=int(config_payload["seed"]),
                refresh=bool(config_payload["refresh"]),
                refresh_bound=int(config_payload["refresh_bound"]),
            ),
            status=ArtifactStatus(payload["status"]),
            layer_index=float(payload["layer_index"]),
            required_lifetime_layers=_optional_int(payload.get("required_lifetime_layers")),
            max_measure_delay_layers=_optional_int(payload.get("max_measure_delay_layers")),
            dgraph_num_nodes=int(payload["dgraph_num_nodes"]),
            dgraph_num_edges=int(payload["dgraph_num_edges"]),
            ff_nodes=tuple(
                FFNode(
                    node_id=int(node_payload["node_id"]),
                    phase=_optional_float(node_payload.get("phase")),
                    node_type=str(node_payload["node_type"]),
                )
                for node_payload in payload["ff_nodes"]
            ),
            ff_edges=tuple(
                FFEdge(
                    src=int(edge_payload["src"]),
                    dst=int(edge_payload["dst"]),
                    dependency=DependencyKind(edge_payload["dependency"]),
                )
                for edge_payload in payload["ff_edges"]
            ),
            ff_chain_depth_raw=int(payload["ff_chain_depth_raw"]),
            ff_chain_depth_shifted=_optional_int(payload.get("ff_chain_depth_shifted")),
            depth_reference=(
                None
                if depth_reference_payload is None
                else DepthReference(
                    kind=ReferenceKind(depth_reference_payload["kind"]),
                    depth=int(depth_reference_payload["depth"]),
                )
            ),
            elapsed_sec=float(payload["elapsed_sec"]),
        )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
