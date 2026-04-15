from __future__ import annotations

import importlib
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from mbqc_ff_evaluator.domain.circuit_models import CZOperation, CircuitProgram, JOperation
from mbqc_ff_evaluator.domain.enums import Algorithm
from mbqc_ff_evaluator.domain.models import ExperimentConfig
from mbqc_ff_evaluator.ports.circuit_factory import CircuitFactory


@dataclass(frozen=True)
class OneAdaptCircuitPayload:
    """OneAdapt-specific payload plus the normalized typed program."""

    logical_qubits: int
    raw_gates: tuple[Any, ...]
    program: CircuitProgram


class OneAdaptCircuitFactory(CircuitFactory):
    """Create reproducible JCZ programs using OneAdapt's reference constructors."""

    def __init__(self, oneadapt_root: Path) -> None:
        self._oneadapt_root = oneadapt_root
        if not self._oneadapt_root.exists():
            raise FileNotFoundError(f"OneAdapt root not found: {self._oneadapt_root}")
        self._ensure_import_path()

    def build_program(self, config: ExperimentConfig) -> CircuitProgram:
        return self.build_payload(config).program

    def build_payload(self, config: ExperimentConfig) -> OneAdaptCircuitPayload:
        self._ensure_import_path()
        numpy_module = importlib.import_module("numpy")
        construct_module = importlib.import_module("OnePerc.Construct_Test_Circuit")

        random.seed(config.seed)
        numpy_module.random.seed(config.seed)

        gates_list, logical_qubits = self._dispatch_construct(construct_module, config)
        raw_gates = tuple(gates_list)
        return OneAdaptCircuitPayload(
            logical_qubits=int(logical_qubits),
            raw_gates=raw_gates,
            program=self._convert_to_program(raw_gates, int(logical_qubits)),
        )

    def _dispatch_construct(
        self,
        construct_module: object,
        config: ExperimentConfig,
    ) -> tuple[list[Any], int]:
        if config.algorithm is Algorithm.QAOA:
            construct = getattr(construct_module, "construct_qaoa")
            return cast(tuple[list[Any], int], construct(config.logical_qubits, 0.5))
        if config.algorithm is Algorithm.QFT:
            construct = getattr(construct_module, "construct_qft")
            return cast(tuple[list[Any], int], construct(config.logical_qubits))
        if config.algorithm is Algorithm.VQE:
            construct = getattr(construct_module, "construct_vqe")
            return cast(tuple[list[Any], int], construct(config.logical_qubits))
        if config.algorithm is Algorithm.GROVER:
            construct = getattr(construct_module, "construct_grover")
            return cast(tuple[list[Any], int], construct(config.logical_qubits))
        if config.algorithm is Algorithm.RCA:
            construct = getattr(construct_module, "construct_rca")
            return cast(tuple[list[Any], int], construct(config.logical_qubits))
        raise ValueError(f"unsupported algorithm: {config.algorithm.value}")

    def _convert_to_program(
        self,
        raw_gates: tuple[Any, ...],
        logical_qubits: int,
    ) -> CircuitProgram:
        operations: list[JOperation | CZOperation] = []
        for gate in raw_gates:
            gate_type = gate.type()
            if gate_type == "J":
                operations.append(
                    JOperation(
                        qubit=int(gate.qubit),
                        phase_quarter_turns=float(gate.phase),
                    )
                )
                continue
            if gate_type == "CZ":
                operations.append(
                    CZOperation(
                        qubit_a=int(gate.qubit1),
                        qubit_b=int(gate.qubit2),
                    )
                )
                continue
            raise ValueError(f"unsupported JCZ gate type: {gate_type}")
        return CircuitProgram(logical_qubits=logical_qubits, operations=tuple(operations))

    def _ensure_import_path(self) -> None:
        oneadapt_path = str(self._oneadapt_root)
        if oneadapt_path not in sys.path:
            sys.path.insert(0, oneadapt_path)
