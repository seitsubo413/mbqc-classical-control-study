from __future__ import annotations

import json
from pathlib import Path

from mbqc_ff_evaluator.cli.prepare_shifted_dag_study import main


def test_prepare_shifted_dag_study_copies_only_selected_subset(tmp_path: Path) -> None:
    source_raw_dir = tmp_path / "baseline_raw"
    source_raw_dir.mkdir()
    ff_study_dir = tmp_path / "ff_study"
    pipeline_study_dir = tmp_path / "pipeline_study"

    _write_artifact(source_raw_dir / "QAOA_H4_Q16_seed0.json", "QAOA", 4, 16, 0)
    _write_artifact(source_raw_dir / "QFT_H8_Q64_seed4.json", "QFT", 8, 64, 4)
    _write_artifact(source_raw_dir / "QAOA_H10_Q100_seed0.json", "QAOA", 10, 100, 0)
    _write_artifact(source_raw_dir / "GROVER_H4_Q16_seed0.json", "GROVER", 4, 16, 0)

    exit_code = main(
        [
            "--source-raw-dir", str(source_raw_dir),
            "--ff-study-dir", str(ff_study_dir),
            "--pipeline-study-dir", str(pipeline_study_dir),
        ]
    )
    assert exit_code == 0

    copied_artifacts = sorted(path.name for path in (ff_study_dir / "artifacts").glob("*.json"))
    assert copied_artifacts == ["QAOA_H4_Q16_seed0.json", "QFT_H8_Q64_seed4.json"]

    ff_manifest = json.loads((ff_study_dir / "manifest.json").read_text(encoding="utf-8"))
    pipeline_manifest = json.loads((pipeline_study_dir / "manifest.json").read_text(encoding="utf-8"))
    assert ff_manifest["selected_artifacts"] == copied_artifacts
    assert pipeline_manifest["selected_artifacts"] == copied_artifacts

    assert (pipeline_study_dir / "summary").exists()
    assert (pipeline_study_dir / "figures").exists()
    assert (pipeline_study_dir / "logs").exists()


def _write_artifact(path: Path, algorithm: str, hardware_size: int, logical_qubits: int, seed: int) -> None:
    payload = {
        "config": {
            "algorithm": algorithm,
            "hardware_size": hardware_size,
            "logical_qubits": logical_qubits,
            "seed": seed,
            "refresh": True,
            "refresh_bound": 20,
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
