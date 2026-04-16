"""Measurement-node scheduling policies."""
from __future__ import annotations

import abc
import random

from mbqc_pipeline_sim.core.scheduler_registry import SchedulerRegistry
from mbqc_pipeline_sim.core.scheduler_signals import (
    build_scheduler_signals,
    refined_stall_aware_issue_limit,
    stall_aware_issue_limit,
)
from mbqc_pipeline_sim.domain.enums import SchedulerRegime, SchedulingPolicy
from mbqc_pipeline_sim.domain.models import PipelineConfig, SimDAG
from mbqc_pipeline_sim.domain.scheduler_models import SchedulerContext, SchedulerDecision
from mbqc_pipeline_sim.ports.scheduler_policy import SchedulerPolicyPort


class SchedulerBase(abc.ABC):
    """Choose nodes to issue from the current ready set."""

    policy_id: SchedulingPolicy

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        self._dag = dag
        self._config = config

    @abc.abstractmethod
    def select(self, context: SchedulerContext) -> SchedulerDecision:
        ...


class ASAPScheduler(SchedulerBase):
    """Issue nodes in topological-level order; ties broken by node-id."""

    policy_id = SchedulingPolicy.ASAP

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        ordered = sorted(context.ready_nodes, key=lambda node: (node.topo_level, node.node_id))
        return _decision_from_views(ordered, context.issue_limit)


class LayerScheduler(SchedulerBase):
    """Only issue nodes from the *lowest* topological level present in *ready*."""

    policy_id = SchedulingPolicy.LAYER

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        if not context.ready_nodes:
            return SchedulerDecision(selected_node_ids=())
        min_level = min(node.topo_level for node in context.ready_nodes)
        same_level = sorted(
            (node for node in context.ready_nodes if node.topo_level == min_level),
            key=lambda node: node.node_id,
        )
        return _decision_from_views(same_level, context.issue_limit)


class GreedyCriticalScheduler(SchedulerBase):
    """Prioritise nodes whose remaining critical path is longest (OoO)."""

    policy_id = SchedulingPolicy.GREEDY_CRITICAL

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        ordered = sorted(
            context.ready_nodes,
            key=lambda node: (-node.remaining_depth, node.node_id),
        )
        return _decision_from_views(ordered, context.issue_limit)


class ShiftedCriticalScheduler(SchedulerBase):
    """Prioritise nodes that are both critical and likely to unlock successors."""

    policy_id = SchedulingPolicy.SHIFTED_CRITICAL

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        ordered = sorted(
            context.ready_nodes,
            key=lambda node: (-node.remaining_depth, -node.unlock_count, node.node_id),
        )
        return _decision_from_views(ordered, context.issue_limit)


class StallAwareShiftedScheduler(SchedulerBase):
    """Shifted-aware scheduler that reacts to FF backpressure."""

    policy_id = SchedulingPolicy.STALL_AWARE_SHIFTED

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        signals = build_scheduler_signals(context)
        effective_limit = stall_aware_issue_limit(context, signals)
        if signals.ff_backpressure_active:
            ordered = sorted(
                context.ready_nodes,
                key=lambda node: (node.unlock_count, -node.remaining_depth, node.node_id),
            )
            return _decision_from_views(
                ordered,
                effective_limit,
                rationale="ff_backpressure",
            )

        ordered = sorted(
            context.ready_nodes,
            key=lambda node: (-node.remaining_depth, -node.unlock_count, node.node_id),
        )
        return _decision_from_views(
            ordered,
            effective_limit,
            rationale="shifted_critical_fallback",
        )


class RefinedStallAwareShiftedScheduler(SchedulerBase):
    """Shifted-aware scheduler with pressure-dependent issue throttling."""

    policy_id = SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        signals = build_scheduler_signals(context)
        effective_limit = refined_stall_aware_issue_limit(context, signals)
        if signals.ff_pressure_score > 0.0:
            ordered = sorted(
                context.ready_nodes,
                key=lambda node: (node.unlock_count, -node.remaining_depth, node.node_id),
            )
            return _decision_from_views(
                ordered,
                effective_limit,
                rationale="ff_pressure_throttled",
            )

        ordered = sorted(
            context.ready_nodes,
            key=lambda node: (-node.remaining_depth, -node.unlock_count, node.node_id),
        )
        return _decision_from_views(
            ordered,
            effective_limit,
            rationale="shifted_critical_fallback",
        )


class RegimeSwitchScheduler(SchedulerBase):
    """Reproducible v1 regime switch used in the original co-design sweep."""

    policy_id = SchedulingPolicy.REGIME_SWITCH

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        super().__init__(dag, config)
        self._asap = ASAPScheduler(dag, config)
        self._shifted_critical = ShiftedCriticalScheduler(dag, config)
        self._stall_aware = StallAwareShiftedScheduler(dag, config)

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        signals = build_scheduler_signals(context)
        if signals.is_ff_bottleneck and signals.ff_backpressure_active:
            decision = self._stall_aware.select(context)
            return SchedulerDecision(
                selected_node_ids=decision.selected_node_ids,
                rationale=SchedulerRegime.STALL_AWARE.value,
            )

        if signals.is_fully_provisioned:
            decision = self._asap.select(context)
            return SchedulerDecision(
                selected_node_ids=decision.selected_node_ids,
                rationale=SchedulerRegime.ASAP.value,
            )

        decision = self._shifted_critical.select(context)
        return SchedulerDecision(
            selected_node_ids=decision.selected_node_ids,
            rationale=SchedulerRegime.SHIFTED_CRITICAL.value,
        )


class RefinedRegimeSwitchScheduler(SchedulerBase):
    """Pressure-aware refinement of the original regime switch heuristic."""

    policy_id = SchedulingPolicy.REGIME_SWITCH_REFINED

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        super().__init__(dag, config)
        self._asap = ASAPScheduler(dag, config)
        self._shifted_critical = ShiftedCriticalScheduler(dag, config)
        self._stall_aware = StallAwareShiftedScheduler(dag, config)

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        signals = build_scheduler_signals(context)
        if signals.recommended_regime is SchedulerRegime.STALL_AWARE:
            decision = self._stall_aware.select(context)
            return SchedulerDecision(
                selected_node_ids=decision.selected_node_ids,
                rationale=SchedulerRegime.STALL_AWARE.value,
            )

        if signals.recommended_regime is SchedulerRegime.ASAP:
            decision = self._asap.select(context)
            return SchedulerDecision(
                selected_node_ids=decision.selected_node_ids,
                rationale=SchedulerRegime.ASAP.value,
            )

        decision = self._shifted_critical.select(context)
        return SchedulerDecision(
            selected_node_ids=decision.selected_node_ids,
            rationale=SchedulerRegime.SHIFTED_CRITICAL.value,
        )


class RandomScheduler(SchedulerBase):
    """Uniformly random selection from ready set (baseline)."""

    policy_id = SchedulingPolicy.RANDOM

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        super().__init__(dag, config)
        self._rng = random.Random(config.seed)

    def select(self, context: SchedulerContext) -> SchedulerDecision:
        pool = list(context.ready_nodes)
        self._rng.shuffle(pool)
        return _decision_from_views(pool, context.issue_limit)


def build_scheduler(
    policy: SchedulingPolicy,
    dag: SimDAG,
    *,
    config: PipelineConfig,
) -> SchedulerPolicyPort:
    return _DEFAULT_REGISTRY.build(policy, dag, config)


def _decision_from_views(
    views: list[object],
    limit: int,
    *,
    rationale: str | None = None,
) -> SchedulerDecision:
    selected = tuple(view.node_id for view in views[:limit])
    return SchedulerDecision(selected_node_ids=selected, rationale=rationale)


def _build_default_registry() -> SchedulerRegistry:
    registry = SchedulerRegistry()
    registry.register(SchedulingPolicy.ASAP, lambda dag, config: ASAPScheduler(dag, config))
    registry.register(SchedulingPolicy.LAYER, lambda dag, config: LayerScheduler(dag, config))
    registry.register(
        SchedulingPolicy.GREEDY_CRITICAL,
        lambda dag, config: GreedyCriticalScheduler(dag, config),
    )
    registry.register(
        SchedulingPolicy.SHIFTED_CRITICAL,
        lambda dag, config: ShiftedCriticalScheduler(dag, config),
    )
    registry.register(
        SchedulingPolicy.STALL_AWARE_SHIFTED,
        lambda dag, config: StallAwareShiftedScheduler(dag, config),
    )
    registry.register(
        SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED,
        lambda dag, config: RefinedStallAwareShiftedScheduler(dag, config),
    )
    registry.register(
        SchedulingPolicy.REGIME_SWITCH,
        lambda dag, config: RegimeSwitchScheduler(dag, config),
    )
    registry.register(
        SchedulingPolicy.REGIME_SWITCH_REFINED,
        lambda dag, config: RefinedRegimeSwitchScheduler(dag, config),
    )
    registry.register(SchedulingPolicy.RANDOM, lambda dag, config: RandomScheduler(dag, config))
    return registry


_DEFAULT_REGISTRY = _build_default_registry()
