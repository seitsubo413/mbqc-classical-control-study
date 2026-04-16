"""Measurement-node scheduling policies."""
from __future__ import annotations

import abc
import math
import random
from dataclasses import dataclass
from typing import Sequence

from mbqc_pipeline_sim.domain.enums import SchedulerRegime, SchedulingPolicy
from mbqc_pipeline_sim.domain.models import PipelineConfig, SimDAG

_LOW_PRESSURE = 0.35
_HIGH_PRESSURE = 0.75


@dataclass(frozen=True)
class SchedulerContext:
    """Per-cycle state that some schedulers use for dynamic priorities."""

    remaining_indegree: dict[int, int]
    ff_waiting_count: int = 0
    ff_in_flight_count: int = 0
    meas_in_flight_count: int = 0


class SchedulerBase(abc.ABC):
    """Pick up to *limit* nodes from *ready* to issue this cycle."""

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        self._dag = dag
        self._config = config

    @abc.abstractmethod
    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        ...


class ASAPScheduler(SchedulerBase):
    """Issue nodes in topological-level order; ties broken by node-id."""

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        ordered = sorted(ready, key=lambda n: (self._dag.topo_level.get(n, 0), n))
        return ordered[:limit]


class LayerScheduler(SchedulerBase):
    """Only issue nodes from the *lowest* topological level present in *ready*."""

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        if not ready:
            return []
        min_level = min(self._dag.topo_level.get(n, 0) for n in ready)
        same_level = [n for n in ready if self._dag.topo_level.get(n, 0) == min_level]
        same_level.sort()
        return same_level[:limit]


class GreedyCriticalScheduler(SchedulerBase):
    """Prioritise nodes whose remaining critical path is longest (OoO)."""

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        ordered = sorted(
            ready,
            key=lambda n: (-self._dag.remaining_depth.get(n, 0), n),
        )
        return ordered[:limit]


class ShiftedCriticalScheduler(SchedulerBase):
    """Prioritise shifted-topology criticality while keeping early layers flowing."""

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        ordered = sorted(
            ready,
            key=lambda n: (
                -self._dag.remaining_depth.get(n, 0),
                self._dag.topo_level.get(n, 0),
                -len(self._dag.adjacency.get(n, [])),
                n,
            ),
        )
        return ordered[:limit]


class StallAwareShiftedScheduler(SchedulerBase):
    """Exploit shifted DAG unlocks when FF width is the active bottleneck."""

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        super().__init__(dag, config)
        self._fallback = ShiftedCriticalScheduler(dag, config)

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        if not ready:
            return []
        if not self._is_ff_bottleneck() or context is None:
            return self._fallback.select(ready, limit, context)

        ordered = sorted(
            ready,
            key=lambda n: (
                -_unlock_count(n, self._dag, context.remaining_indegree),
                -self._dag.remaining_depth.get(n, 0),
                self._dag.topo_level.get(n, 0),
                -len(self._dag.adjacency.get(n, [])),
                n,
            ),
        )
        return ordered[:limit]

    def _is_ff_bottleneck(self) -> bool:
        ff_width = self._config.ff_width
        if ff_width is None:
            return False
        if ff_width < self._config.issue_width:
            return True
        meas_width = self._config.meas_width
        return meas_width is not None and ff_width < meas_width


class RefinedStallAwareShiftedScheduler(SchedulerBase):
    """Pressure-proportional issue throttling on top of StallAwareShifted."""

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        super().__init__(dag, config)
        self._base = StallAwareShiftedScheduler(dag, config)

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        effective_limit = self._throttled_limit(limit, context)
        return self._base.select(ready, effective_limit, context)

    def _throttled_limit(self, limit: int, context: SchedulerContext | None) -> int:
        ff_width = self._config.ff_width
        if ff_width is None or ff_width >= limit or context is None:
            return limit
        if not self._base._is_ff_bottleneck():
            return limit

        pressure = _ff_pressure_score(context, ff_width)
        if pressure <= _LOW_PRESSURE:
            return limit
        if pressure >= _HIGH_PRESSURE:
            return ff_width

        progress = (pressure - _LOW_PRESSURE) / (_HIGH_PRESSURE - _LOW_PRESSURE)
        scaled = limit - math.ceil(progress * (limit - ff_width))
        return max(ff_width, min(limit, scaled))


class RegimeSwitchScheduler(SchedulerBase):
    """Switch between ASAP / ShiftedCritical / StallAware based on runtime regime."""

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        super().__init__(dag, config)
        self._asap = ASAPScheduler(dag, config)
        self._shifted = ShiftedCriticalScheduler(dag, config)
        self._stall = StallAwareShiftedScheduler(dag, config)

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        regime = self._recommend_regime(context)
        if regime is SchedulerRegime.STALL_AWARE:
            return self._stall.select(ready, limit, context)
        if regime is SchedulerRegime.ASAP:
            return self._asap.select(ready, limit, context)
        return self._shifted.select(ready, limit, context)

    def _recommend_regime(self, context: SchedulerContext | None) -> SchedulerRegime:
        if self._stall._is_ff_bottleneck() and context is not None and context.ff_waiting_count > 0:
            return SchedulerRegime.STALL_AWARE
        if self._is_fully_provisioned() and (context is None or context.ff_waiting_count == 0):
            return SchedulerRegime.ASAP
        return SchedulerRegime.SHIFTED_CRITICAL

    def _is_fully_provisioned(self) -> bool:
        issue = self._config.issue_width
        eff_meas = self._config.meas_width if self._config.meas_width is not None else issue
        eff_ff = self._config.ff_width if self._config.ff_width is not None else issue
        return eff_meas >= issue and eff_ff >= issue


class RefinedRegimeSwitchScheduler(SchedulerBase):
    """Pressure-aware refinement: uses ff_pressure_score to guide regime selection."""

    def __init__(self, dag: SimDAG, config: PipelineConfig) -> None:
        super().__init__(dag, config)
        self._asap = ASAPScheduler(dag, config)
        self._shifted = ShiftedCriticalScheduler(dag, config)
        self._stall = StallAwareShiftedScheduler(dag, config)

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        regime = self._recommend_regime(context)
        if regime is SchedulerRegime.STALL_AWARE:
            return self._stall.select(ready, limit, context)
        if regime is SchedulerRegime.ASAP:
            return self._asap.select(ready, limit, context)
        return self._shifted.select(ready, limit, context)

    def _recommend_regime(self, context: SchedulerContext | None) -> SchedulerRegime:
        ff_width = self._config.ff_width
        if ff_width is None or context is None:
            return SchedulerRegime.SHIFTED_CRITICAL

        is_bottleneck = self._stall._is_ff_bottleneck()
        pressure = _ff_pressure_score(context, ff_width)

        if is_bottleneck and pressure >= _HIGH_PRESSURE:
            return SchedulerRegime.STALL_AWARE

        issue = self._config.issue_width
        eff_meas = self._config.meas_width if self._config.meas_width is not None else issue
        eff_ff = self._config.ff_width if self._config.ff_width is not None else issue
        if eff_meas >= issue and eff_ff >= issue and pressure <= _LOW_PRESSURE:
            return SchedulerRegime.ASAP
        return SchedulerRegime.SHIFTED_CRITICAL


class RandomScheduler(SchedulerBase):
    """Uniformly random selection from ready set (baseline)."""

    def __init__(self, dag: SimDAG, config: PipelineConfig, *, seed: int = 0) -> None:
        super().__init__(dag, config)
        self._rng = random.Random(seed)

    def select(
        self,
        ready: Sequence[int],
        limit: int,
        context: SchedulerContext | None = None,
    ) -> list[int]:
        pool = list(ready)
        self._rng.shuffle(pool)
        return pool[:limit]


def build_scheduler(
    policy: SchedulingPolicy,
    dag: SimDAG,
    config: PipelineConfig,
    *,
    seed: int = 0,
) -> SchedulerBase:
    if policy == SchedulingPolicy.ASAP:
        return ASAPScheduler(dag, config)
    if policy == SchedulingPolicy.LAYER:
        return LayerScheduler(dag, config)
    if policy == SchedulingPolicy.GREEDY_CRITICAL:
        return GreedyCriticalScheduler(dag, config)
    if policy == SchedulingPolicy.SHIFTED_CRITICAL:
        return ShiftedCriticalScheduler(dag, config)
    if policy == SchedulingPolicy.STALL_AWARE_SHIFTED:
        return StallAwareShiftedScheduler(dag, config)
    if policy == SchedulingPolicy.STALL_AWARE_SHIFTED_REFINED:
        return RefinedStallAwareShiftedScheduler(dag, config)
    if policy == SchedulingPolicy.REGIME_SWITCH:
        return RegimeSwitchScheduler(dag, config)
    if policy == SchedulingPolicy.REGIME_SWITCH_REFINED:
        return RefinedRegimeSwitchScheduler(dag, config)
    if policy == SchedulingPolicy.RANDOM:
        return RandomScheduler(dag, config, seed=seed)
    raise ValueError(f"Unknown policy: {policy}")


# ── module-level helpers ──────────────────────────────────────────────────────

def _unlock_count(node_id: int, dag: SimDAG, remaining_indegree: dict[int, int]) -> int:
    return sum(
        1
        for succ in dag.adjacency.get(node_id, [])
        if remaining_indegree.get(succ, 0) == 1
    )


def _ff_pressure_score(context: SchedulerContext, ff_width: int) -> float:
    queue_p = min(context.ff_waiting_count / ff_width, 1.0)
    meas_p = min(context.meas_in_flight_count / ff_width, 1.0)
    ff_p = min(context.ff_in_flight_count / ff_width, 1.0)
    return round((queue_p + meas_p + ff_p) / 3.0, 6)
