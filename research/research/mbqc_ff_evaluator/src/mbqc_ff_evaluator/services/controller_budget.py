from __future__ import annotations

from collections.abc import Iterable

from mbqc_ff_evaluator.analysis.models import BudgetRow
from mbqc_ff_evaluator.domain.controller_models import ControllerEvaluation, ControllerModel


def controller_stage_latency_ns(model: ControllerModel) -> float:
    cycle_latency_ns = 0.0
    if model.cycles_per_stage > 0:
        cycle_latency_ns = model.cycles_per_stage * (1000.0 / model.clock_mhz)
    return model.fixed_overhead_ns + cycle_latency_ns


def evaluate_budget(
    *,
    row: BudgetRow,
    budget_kind: str,
    budget_ns: float,
    model: ControllerModel,
) -> ControllerEvaluation:
    controller_latency = controller_stage_latency_ns(model)
    slack_ns = budget_ns - controller_latency
    return ControllerEvaluation(
        algorithm=row.algorithm,
        hardware_size=row.hardware_size,
        logical_qubits=row.logical_qubits,
        tau_ph_us=row.tau_ph_us,
        budget_kind=budget_kind,
        budget_ns=budget_ns,
        controller_name=model.name,
        controller_latency_ns=controller_latency,
        slack_ns=slack_ns,
        feasible=slack_ns >= 0.0,
    )


def evaluate_budget_row(
    row: BudgetRow,
    models: Iterable[ControllerModel],
) -> list[ControllerEvaluation]:
    budget_values = {
        "dependency": row.t_ff_cond_ns_median,
        "shifted_dependency": row.t_ff_shifted_ns_median,
        "hold": row.t_hold_ns_median,
        "measurement": row.t_meas_ns_median,
        "conservative": row.t_cons_ns_median,
    }
    evaluations: list[ControllerEvaluation] = []
    for budget_kind, budget_ns in budget_values.items():
        if budget_ns is None:
            continue
        for model in models:
            evaluations.append(
                evaluate_budget(
                    row=row,
                    budget_kind=budget_kind,
                    budget_ns=budget_ns,
                    model=model,
                )
            )
    return evaluations
