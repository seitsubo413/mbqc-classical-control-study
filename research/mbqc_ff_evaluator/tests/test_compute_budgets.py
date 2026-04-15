from __future__ import annotations

import math

from mbqc_ff_evaluator.services.compute_budgets import (
    compute_conservative_budget,
    compute_dependency_budget,
    compute_layer_budget,
    convert_latency_budget_to_clock,
)


def test_compute_dependency_budget() -> None:
    budget = compute_dependency_budget(dependency_depth=4, photon_lifetime_us=1.0)
    assert budget.t_ff_cond_ns == 250.0


def test_compute_dependency_budget_zero_depth_is_inf() -> None:
    budget = compute_dependency_budget(dependency_depth=0, photon_lifetime_us=1.0)
    assert math.isinf(budget.t_ff_cond_ns)


def test_compute_layer_budget() -> None:
    budget = compute_layer_budget(layer_metric=5, photon_lifetime_us=1.0)
    assert budget.per_layer_budget_ns == 200.0


def test_compute_conservative_budget() -> None:
    dependency_budget = compute_dependency_budget(dependency_depth=4, photon_lifetime_us=1.0)
    hold_budget = compute_layer_budget(layer_metric=5, photon_lifetime_us=1.0)
    meas_budget = compute_layer_budget(layer_metric=10, photon_lifetime_us=1.0)
    conservative = compute_conservative_budget(dependency_budget, hold_budget, meas_budget)
    assert conservative.t_cons_ns == 100.0


def test_convert_latency_budget_to_clock() -> None:
    assert convert_latency_budget_to_clock(latency_ns=250.0, cycles_per_stage=1) == 4.0
