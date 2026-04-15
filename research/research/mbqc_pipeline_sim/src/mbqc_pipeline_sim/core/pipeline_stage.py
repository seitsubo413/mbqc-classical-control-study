"""Simple latency-pipeline models for measurement and FF processing."""
from __future__ import annotations

from collections import deque
from typing import Sequence


class LatencyPipeline:
    """Models a pipelined stage with fixed latency and optional width.

    Each enqueued item takes *latency* calls to ``advance()`` before it
    appears in the output list.

    The stage is fully pipelined: it can accept up to ``width`` items per
    cycle and produces the corresponding completions after ``latency``
    cycles.  ``width=None`` means unlimited ingress bandwidth.
    """

    def __init__(self, latency: int, *, width: int | None = None) -> None:
        if latency <= 0:
            raise ValueError("latency must be positive")
        if width is not None and width <= 0:
            raise ValueError("width must be positive when provided")
        self._latency = latency
        self._width = width
        self._stages: deque[list[int]] = deque([[] for _ in range(latency)])

    @property
    def occupancy(self) -> int:
        return sum(len(stage) for stage in self._stages)

    @property
    def available_input_slots(self) -> int | None:
        if self._width is None:
            return None
        return max(self._width - len(self._stages[-1]), 0)

    def enqueue_many(self, node_ids: Sequence[int]) -> list[int]:
        if not node_ids:
            return []
        limit = self.available_input_slots
        admitted = list(node_ids if limit is None else node_ids[:limit])
        self._stages[-1].extend(admitted)
        return admitted

    def advance(self) -> list[int]:
        """Tick one cycle. Return node-ids that completed this cycle."""
        completed = list(self._stages.popleft())
        self._stages.append([])
        return completed
