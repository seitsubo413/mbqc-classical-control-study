from __future__ import annotations

from enum import Enum


class SchedulingPolicy(str, Enum):
    ASAP = "asap"
    LAYER = "layer"
    GREEDY_CRITICAL = "greedy_critical"
    SHIFTED_CRITICAL = "shifted_critical"
    STALL_AWARE_SHIFTED = "stall_aware_shifted"
    RANDOM = "random"


class ReleaseMode(str, Enum):
    SAME_CYCLE = "same_cycle"
    NEXT_CYCLE = "next_cycle"


class DagVariant(str, Enum):
    RAW = "raw"
    SHIFTED = "shifted"


class NodeState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    IN_FLIGHT_MEAS = "in_flight_meas"
    WAITING_FF = "waiting_ff"
    IN_FLIGHT_FF = "in_flight_ff"
    DONE = "done"
