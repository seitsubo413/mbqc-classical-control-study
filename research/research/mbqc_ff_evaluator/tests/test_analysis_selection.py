from __future__ import annotations

from mbqc_ff_evaluator.analysis.models import BudgetRow, BudgetSelection
from mbqc_ff_evaluator.analysis.selection import filter_budget_rows, is_coupled_configuration
from mbqc_ff_evaluator.domain.enums import BudgetSelectionMode, ConstraintKind


def test_is_coupled_configuration() -> None:
    assert is_coupled_configuration(4, 16) is True
    assert is_coupled_configuration(8, 36) is False


def test_filter_budget_rows_coupled_only() -> None:
    rows = [
        BudgetRow(
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
        ),
        BudgetRow(
            algorithm="QAOA",
            hardware_size=8,
            logical_qubits=36,
            tau_ph_us=1.0,
            n_seeds=5,
            is_coupled=False,
            depth_raw_median=76.0,
            depth_raw_q1=73.0,
            depth_raw_q3=80.0,
            t_ff_cond_ns_median=13.1,
            t_ff_cond_ns_q1=12.4,
            t_ff_cond_ns_q3=13.7,
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
            meas_median=27.0,
            t_hold_ns_median=34.4,
            t_hold_ns_q1=33.0,
            t_hold_ns_q3=35.0,
            t_meas_ns_median=37.0,
            t_meas_ns_q1=36.0,
            t_meas_ns_q3=38.0,
            t_cons_ns_median=13.1,
            t_cons_ns_q1=12.4,
            t_cons_ns_q3=13.7,
            dominant_constraint=ConstraintKind.DEPENDENCY,
        ),
    ]
    selection = BudgetSelection(mode=BudgetSelectionMode.COUPLED_ONLY, tau_ph_us=1.0)
    filtered = filter_budget_rows(rows, selection)
    assert len(filtered) == 1
    assert filtered[0].hardware_size == 4
