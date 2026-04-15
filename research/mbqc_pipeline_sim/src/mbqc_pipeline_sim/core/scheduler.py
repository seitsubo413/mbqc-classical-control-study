"""Measurement-node scheduling policies."""
from __future__ import annotations

import abc
import random
from typing import Sequence

from mbqc_pipeline_sim.domain.enums import SchedulingPolicy
from mbqc_pipeline_sim.domain.models import SimDAG


class SchedulerBase(abc.ABC):
    """Pick up to *limit* nodes from *ready* to issue this cycle."""

    def __init__(self, dag: SimDAG) -> None:
        self._dag = dag

    @abc.abstractmethod
    def select(self, ready: Sequence[int], limit: int) -> list[int]:
        ...


class ASAPScheduler(SchedulerBase):
    """Issue nodes in topological-level order; ties broken by node-id."""

    def select(self, ready: Sequence[int], limit: int) -> list[int]:
        ordered = sorted(ready, key=lambda n: (self._dag.topo_level.get(n, 0), n))
        return ordered[:limit]


class LayerScheduler(SchedulerBase):
    """Only issue nodes from the *lowest* topological level present in *ready*."""

    def select(self, ready: Sequence[int], limit: int) -> list[int]:
        if not ready:
            return []
        min_level = min(self._dag.topo_level.get(n, 0) for n in ready)
        same_level = [n for n in ready if self._dag.topo_level.get(n, 0) == min_level]
        same_level.sort()
        return same_level[:limit]


class GreedyCriticalScheduler(SchedulerBase):
    """Prioritise nodes whose remaining critical path is longest (OoO)."""

    def select(self, ready: Sequence[int], limit: int) -> list[int]:
        ordered = sorted(
            ready,
            key=lambda n: (-self._dag.remaining_depth.get(n, 0), n),
        )
        return ordered[:limit]


class RandomScheduler(SchedulerBase):
    """Uniformly random selection from ready set (baseline)."""

    def __init__(self, dag: SimDAG, *, seed: int = 0) -> None:
        super().__init__(dag)
        self._rng = random.Random(seed)

    def select(self, ready: Sequence[int], limit: int) -> list[int]:
        pool = list(ready)
        self._rng.shuffle(pool)
        return pool[:limit]


def build_scheduler(policy: SchedulingPolicy, dag: SimDAG, *, seed: int = 0) -> SchedulerBase:
    if policy == SchedulingPolicy.ASAP:
        return ASAPScheduler(dag)
    if policy == SchedulingPolicy.LAYER:
        return LayerScheduler(dag)
    if policy == SchedulingPolicy.GREEDY_CRITICAL:
        return GreedyCriticalScheduler(dag)
    if policy == SchedulingPolicy.RANDOM:
        return RandomScheduler(dag, seed=seed)
    raise ValueError(f"Unknown policy: {policy}")
