from __future__ import annotations

from enum import Enum


class Algorithm(str, Enum):
    QAOA = "QAOA"
    QFT = "QFT"
    VQE = "VQE"
    GROVER = "Grover"
    RCA = "RCA"


class DependencyKind(str, Enum):
    X = "x"
    Z = "z"


class ArtifactStatus(str, Enum):
    SUCCESS = "success"
    TIMEOUT_GUARD = "timeout_guard"
    DAG_ERROR = "dag_error"
    EXCEPTION = "exception"


class ReferenceKind(str, Enum):
    EXACT_GRAPH = "exact_graph"
    INDEPENDENT_COMPILER = "independent_compiler"


class ConstraintKind(str, Enum):
    DEPENDENCY = "dependency"
    HOLD = "hold"
    MEASUREMENT = "measurement"


class BudgetSelectionMode(str, Enum):
    ALL = "all"
    COUPLED_ONLY = "coupled_only"
    FIXED_H = "fixed_h"
    FIXED_Q = "fixed_q"
