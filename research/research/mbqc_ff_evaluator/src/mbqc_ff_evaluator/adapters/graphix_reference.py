from __future__ import annotations

import os
from pathlib import Path

from mbqc_ff_evaluator.adapters.graphix_translation import extract_graphix_gflow_depth
from mbqc_ff_evaluator.adapters.oneadapt_circuit_factory import OneAdaptCircuitFactory
from mbqc_ff_evaluator.domain.enums import Algorithm, ReferenceKind
from mbqc_ff_evaluator.domain.models import DepthReference, ExperimentConfig
from mbqc_ff_evaluator.ports.depth_reference import DepthReferenceBackend
from mbqc_ff_evaluator.ports.circuit_factory import CircuitFactory


class GraphixReferenceBackend(DepthReferenceBackend):
    """Independent graphix-based reference depth computation."""

    def __init__(
        self,
        oneadapt_root: Path | None = None,
        *,
        circuit_factory: CircuitFactory | None = None,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[5]
        resolved_oneadapt_root = oneadapt_root or repo_root / "OneAdapt_AE 2"
        cache_dir = repo_root / "research" / "mbqc_ff_evaluator" / ".cache" / "matplotlib"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
        self._circuit_factory = circuit_factory or OneAdaptCircuitFactory(resolved_oneadapt_root)

    def compute_reference(self, config: ExperimentConfig) -> DepthReference | None:
        if config.algorithm is Algorithm.GROVER:
            return None
        try:
            program = self._circuit_factory.build_program(config)
            depth = extract_graphix_gflow_depth(program)
        except ModuleNotFoundError:
            return None
        return DepthReference(kind=ReferenceKind.INDEPENDENT_COMPILER, depth=depth)
