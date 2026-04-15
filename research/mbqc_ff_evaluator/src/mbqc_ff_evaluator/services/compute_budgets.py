from __future__ import annotations

import math

from mbqc_ff_evaluator.domain.models import ConservativeBudget, DependencyBudget, LayerBudget


def compute_dependency_budget(dependency_depth: int, photon_lifetime_us: float) -> DependencyBudget:
    if dependency_depth < 0:
        raise ValueError("dependency_depth must be non-negative")
    if photon_lifetime_us <= 0:
        raise ValueError("photon_lifetime_us must be positive")

    photon_lifetime_ns = photon_lifetime_us * 1000.0
    budget = math.inf if dependency_depth == 0 else photon_lifetime_ns / dependency_depth
    return DependencyBudget(
        dependency_depth=dependency_depth,
        photon_lifetime_us=photon_lifetime_us,
        t_ff_cond_ns=budget,
    )


def compute_layer_budget(layer_metric: int, photon_lifetime_us: float) -> LayerBudget:
    if layer_metric < 0:
        raise ValueError("layer_metric must be non-negative")
    if photon_lifetime_us <= 0:
        raise ValueError("photon_lifetime_us must be positive")

    photon_lifetime_ns = photon_lifetime_us * 1000.0
    budget = math.inf if layer_metric == 0 else photon_lifetime_ns / layer_metric
    return LayerBudget(
        layer_metric=layer_metric,
        photon_lifetime_us=photon_lifetime_us,
        per_layer_budget_ns=budget,
    )


def compute_conservative_budget(
    dependency_budget: DependencyBudget,
    hold_budget: LayerBudget,
    meas_budget: LayerBudget,
) -> ConservativeBudget:
    t_cons_ns = min(
        dependency_budget.t_ff_cond_ns,
        hold_budget.per_layer_budget_ns,
        meas_budget.per_layer_budget_ns,
    )
    return ConservativeBudget(
        dependency_budget_ns=dependency_budget.t_ff_cond_ns,
        hold_budget_ns=hold_budget.per_layer_budget_ns,
        meas_budget_ns=meas_budget.per_layer_budget_ns,
        t_cons_ns=t_cons_ns,
    )


def convert_latency_budget_to_clock(latency_ns: float, cycles_per_stage: int) -> float:
    if cycles_per_stage <= 0:
        raise ValueError("cycles_per_stage must be positive")
    if math.isinf(latency_ns):
        return 0.0
    if latency_ns <= 0:
        raise ValueError("latency_ns must be positive or inf")
    return 1000.0 * cycles_per_stage / latency_ns
