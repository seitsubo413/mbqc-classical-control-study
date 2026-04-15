from __future__ import annotations

from mbqc_ff_evaluator.analysis.models import BudgetRow
from mbqc_ff_evaluator.domain.controller_models import ControllerModel
from mbqc_ff_evaluator.domain.enums import ConstraintKind
from mbqc_ff_evaluator.services.controller_budget import controller_stage_latency_ns, evaluate_budget_row


def _budget_row() -> BudgetRow:
    return BudgetRow(
        algorithm="QAOA",
        hardware_size=4,
        logical_qubits=16,
        tau_ph_us=1.0,
        n_seeds=5,
        is_coupled=True,
        depth_raw_median=34.0,
        depth_raw_q1=30.0,
        depth_raw_q3=36.0,
        t_ff_cond_ns_median=29.4,
        t_ff_cond_ns_q1=28.0,
        t_ff_cond_ns_q3=34.0,
        depth_shifted_median=2.0,
        depth_shifted_q1=2.0,
        depth_shifted_q3=2.0,
        depth_reference_kind=None,
        depth_reference_median=None,
        depth_reference_q1=None,
        depth_reference_q3=None,
        t_ff_shifted_ns_median=500.0,
        t_ff_shifted_ns_q1=500.0,
        t_ff_shifted_ns_q3=500.0,
        hold_median=29.0,
        meas_median=26.0,
        t_hold_ns_median=34.4,
        t_hold_ns_q1=33.0,
        t_hold_ns_q3=35.0,
        t_meas_ns_median=38.4,
        t_meas_ns_q1=37.0,
        t_meas_ns_q3=39.0,
        t_cons_ns_median=29.4,
        t_cons_ns_q1=28.0,
        t_cons_ns_q3=34.0,
        dominant_constraint=ConstraintKind.DEPENDENCY,
    )


def test_controller_stage_latency_ns_uses_clock_and_cycles() -> None:
    model = ControllerModel(name="clocked_2ghz_5cy", clock_mhz=2000.0, cycles_per_stage=5)
    assert controller_stage_latency_ns(model) == 2.5


def test_evaluate_budget_row_produces_feasibility_rows() -> None:
    model = ControllerModel(name="cmos_10ns_target", clock_mhz=1000.0, cycles_per_stage=0, fixed_overhead_ns=10.0)
    evaluations = evaluate_budget_row(_budget_row(), [model])
    by_kind = {evaluation.budget_kind: evaluation for evaluation in evaluations}
    assert by_kind["dependency"].feasible is True
    assert by_kind["dependency"].slack_ns > 0.0
    assert by_kind["shifted_dependency"].feasible is True
