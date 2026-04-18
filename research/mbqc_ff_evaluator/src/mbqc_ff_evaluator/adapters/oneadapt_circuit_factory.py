from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

import numpy

from mbqc_graph_compiler.circuit_constructors import (
    construct_bv,
    construct_grover,
    construct_qaoa,
    construct_qft,
    construct_rca,
    construct_vqe,
)
from mbqc_ff_evaluator.domain.circuit_models import CZOperation, CircuitProgram, JOperation
from mbqc_ff_evaluator.domain.enums import Algorithm
from mbqc_ff_evaluator.domain.models import ExperimentConfig
from mbqc_ff_evaluator.ports.circuit_factory import CircuitFactory


@dataclass(frozen=True)
class OneAdaptCircuitPayload:
    """JCZ circuit payload with normalized typed program."""

    logical_qubits: int
    raw_gates: tuple[Any, ...]
    program: CircuitProgram


class OneAdaptCircuitFactory(CircuitFactory):
    """Create reproducible JCZ programs using mbqc_graph_compiler constructors."""

    def build_program(self, config: ExperimentConfig) -> CircuitProgram:
        return self.build_payload(config).program

    def build_payload(self, config: ExperimentConfig) -> OneAdaptCircuitPayload:
        random.seed(config.seed)
        numpy.random.seed(config.seed)

        gates_list, logical_qubits = self._dispatch_construct(config)
        raw_gates = tuple(gates_list)
        return OneAdaptCircuitPayload(
            logical_qubits=int(logical_qubits),
            raw_gates=raw_gates,
            program=self._convert_to_program(raw_gates, int(logical_qubits)),
        )

    def _dispatch_construct(self, config: ExperimentConfig) -> tuple[list[Any], int]:
        if config.algorithm is Algorithm.QAOA:
            return construct_qaoa(config.logical_qubits, 0.5)
        if config.algorithm is Algorithm.QFT:
            return construct_qft(config.logical_qubits)
        if config.algorithm is Algorithm.VQE:
            return construct_vqe(config.logical_qubits)
        if config.algorithm is Algorithm.GROVER:
            return construct_grover(config.logical_qubits)
        if config.algorithm is Algorithm.RCA:
            return construct_rca(config.logical_qubits)
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
