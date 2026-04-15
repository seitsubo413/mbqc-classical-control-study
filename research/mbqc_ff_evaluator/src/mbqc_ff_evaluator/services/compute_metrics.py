from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

from mbqc_ff_evaluator.domain.errors import DependencyGraphError
from mbqc_ff_evaluator.domain.models import FFEdge


def validate_dag(node_ids: Iterable[int], edges: Iterable[FFEdge]) -> None:
    """Raise if the graph contains a cycle."""
    _compute_longest_path_length(tuple(node_ids), tuple(edges), fail_on_cycle=True)


def compute_ff_chain_depth_raw(node_ids: Iterable[int], edges: Iterable[FFEdge]) -> int:
    """Compute the raw dependency depth as the longest path length of a DAG."""
    return _compute_longest_path_length(tuple(node_ids), tuple(edges), fail_on_cycle=True)


def compute_ff_chain_depth_shifted(node_ids: Iterable[int], edges: Iterable[FFEdge]) -> int:
    """Compute the shifted dependency depth.

    Signal-shift transformation itself belongs in the adapter layer. This function only
    operates on the transformed graph passed to it.
    """
    return _compute_longest_path_length(tuple(node_ids), tuple(edges), fail_on_cycle=True)


def _compute_longest_path_length(
    node_ids: tuple[int, ...],
    edges: tuple[FFEdge, ...],
    *,
    fail_on_cycle: bool,
) -> int:
    adjacency: dict[int, list[int]] = defaultdict(list)
    indegree: dict[int, int] = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        adjacency[edge.src].append(edge.dst)
        indegree.setdefault(edge.src, 0)
        indegree[edge.dst] = indegree.get(edge.dst, 0) + 1

    queue: deque[int] = deque(node_id for node_id, degree in indegree.items() if degree == 0)
    distance: dict[int, int] = {node_id: 0 for node_id in indegree}
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in adjacency.get(node, []):
            distance[neighbor] = max(distance[neighbor], distance[node] + 1)
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if fail_on_cycle and visited != len(indegree):
        raise DependencyGraphError("dependency graph must be a DAG")

    return max(distance.values(), default=0)
