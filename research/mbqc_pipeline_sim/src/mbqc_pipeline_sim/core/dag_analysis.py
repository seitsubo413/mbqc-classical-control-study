"""Static DAG analysis utilities — ILP profile, width per level, etc."""
from __future__ import annotations

from collections import Counter

from mbqc_pipeline_sim.domain.models import SimDAG


def level_width_histogram(dag: SimDAG) -> dict[int, int]:
    """Return {topo_level: number_of_nodes_at_that_level}."""
    return dict(Counter(dag.topo_level.values()))


def max_parallelism(dag: SimDAG) -> int:
    """Maximum number of nodes at any single topological level."""
    hist = level_width_histogram(dag)
    return max(hist.values()) if hist else 0


def theoretical_min_cycles(dag: SimDAG, issue_width: int) -> int:
    """Lower bound on total cycles, ignoring FF latency.

    Each level must consume at least ceil(width / W) cycles.
    """
    import math

    hist = level_width_histogram(dag)
    return sum(math.ceil(w / issue_width) for w in hist.values())


def critical_path_length(dag: SimDAG) -> int:
    """Longest path through the DAG (= max topological level)."""
    return max(dag.topo_level.values(), default=0)
