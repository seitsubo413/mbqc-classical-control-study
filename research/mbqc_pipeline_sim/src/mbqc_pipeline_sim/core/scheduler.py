"""Measurement-node scheduling policies."""
from __future__ import annotations

import abc
from dataclasses import dataclass
import random
from typing import Sequence

from mbqc_pipeline_sim.domain.enums import SchedulingPolicy
from mbqc_pipeline_sim.domain.models import PipelineConfig, SimDAG


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
                -self._unlock_count(n, context.remaining_indegree),
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

    def _unlock_count(self, node_id: int, remaining_indegree: dict[int, int]) -> int:
        return sum(
            1
            for succ in self._dag.adjacency.get(node_id, [])
            if remaining_indegree.get(succ, 0) == 1
        )


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
    if policy == SchedulingPolicy.RANDOM:
        return RandomScheduler(dag, config, seed=seed)
    raise ValueError(f"Unknown policy: {policy}")
