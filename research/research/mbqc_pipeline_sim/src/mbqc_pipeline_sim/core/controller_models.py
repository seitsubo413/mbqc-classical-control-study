"""Reference controller specifications for feasibility analysis."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControllerSpec:
    name: str
    t_ff_ns: float
    description: str


OPX = ControllerSpec(
    name="OPX",
    t_ff_ns=250.0,
    description="Quantum Machines OPX+ (real-time classical processing)",
)

XCOM = ControllerSpec(
    name="XCOM",
    t_ff_ns=185.0,
    description="Fermilab XCOM (cryo-CMOS real-time controller)",
)

CUSTOM_FAST = ControllerSpec(
    name="Custom-100ns",
    t_ff_ns=100.0,
    description="Hypothetical fast MBQC controller",
)

CUSTOM_ULTRAFAST = ControllerSpec(
    name="Custom-50ns",
    t_ff_ns=50.0,
    description="Hypothetical ultra-fast MBQC controller",
)

ALL_CONTROLLERS = [OPX, XCOM, CUSTOM_FAST, CUSTOM_ULTRAFAST]


def is_feasible(
    d_ff: int,
    tau_ph_us: float,
    controller: ControllerSpec,
) -> bool:
    """Check if the controller can meet the FF budget for the given depth."""
    if d_ff <= 0:
        return True
    t_budget_ns = (tau_ph_us * 1000.0) / d_ff
    return controller.t_ff_ns <= t_budget_ns
