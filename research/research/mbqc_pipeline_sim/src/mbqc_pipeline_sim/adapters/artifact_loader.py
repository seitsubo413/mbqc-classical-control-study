"""Load FF evaluator JSON artifacts and convert them into SimDAG."""
from __future__ import annotations

import json
import warnings
from collections import defaultdict, deque
from pathlib import Path

from mbqc_pipeline_sim.domain.errors import InvalidArtifactError
from mbqc_pipeline_sim.domain.models import MeasEdge, MeasNode, SimDAG


def load_dag_from_json(path: Path) -> SimDAG:
    """Read a single FF-evaluator artifact JSON and build a SimDAG."""
    with open(path) as f:
        raw = json.load(f)

    config = raw["config"]
    nodes = tuple(
        MeasNode(
            node_id=int(n["node_id"]),
            phase=n.get("phase"),
            node_type=n.get("node_type", "Unknown"),
        )
        for n in raw["ff_nodes"]
    )
    edges = tuple(
        MeasEdge(src=int(e["src"]), dst=int(e["dst"]), dependency=e["dependency"])
        for e in raw["ff_edges"]
    )

    dag = SimDAG(
        nodes=nodes,
        edges=edges,
        num_nodes=len(nodes),
        num_edges=len(edges),
        algorithm=config["algorithm"],
        hardware_size=config["hardware_size"],
        logical_qubits=config["logical_qubits"],
        dag_seed=config["seed"],
        ff_chain_depth_raw=raw.get("ff_chain_depth_raw", 0),
        ff_chain_depth_shifted=raw.get("ff_chain_depth_shifted"),
    )
    _preprocess(dag)
    return dag


def load_all_dags(directory: Path) -> list[SimDAG]:
    """Load every *.json artifact in *directory*."""
    dags: list[SimDAG] = []
    for p in sorted(directory.glob("*.json")):
        try:
            dags.append(load_dag_from_json(p))
        except (KeyError, json.JSONDecodeError) as exc:
            warnings.warn(f"Skipping {p.name}: {exc}", stacklevel=2)
            continue
    return dags


def _preprocess(dag: SimDAG) -> None:
    """Build adjacency, indegree, topological levels, and remaining-depth."""
    node_ids = {n.node_id for n in dag.nodes}
    adj: dict[int, list[int]] = defaultdict(list)
    rev: dict[int, list[int]] = defaultdict(list)
    indeg: dict[int, int] = {nid: 0 for nid in node_ids}

    for e in dag.edges:
        if e.src not in node_ids or e.dst not in node_ids:
            raise InvalidArtifactError(
                f"Edge {e.src}->{e.dst} references a node that does not exist"
            )
        adj[e.src].append(e.dst)
        rev[e.dst].append(e.src)
        indeg[e.dst] = indeg.get(e.dst, 0) + 1

    dag.adjacency = dict(adj)
    dag.reverse_adj = dict(rev)
    dag.indegree = indeg

    # Forward BFS → topological level (depth from sources)
    topo: dict[int, int] = {nid: 0 for nid in node_ids}
    queue: deque[int] = deque(nid for nid, d in indeg.items() if d == 0)
    tmp_indeg = dict(indeg)
    processed = 0
    while queue:
        n = queue.popleft()
        processed += 1
        for succ in adj.get(n, []):
            topo[succ] = max(topo[succ], topo[n] + 1)
            tmp_indeg[succ] -= 1
            if tmp_indeg[succ] == 0:
                queue.append(succ)
    if processed != len(node_ids):
        raise InvalidArtifactError("Dependency graph is not acyclic")
    dag.topo_level = topo

    # Backward BFS → remaining depth (longest path to any sink)
    outdegree: dict[int, int] = {nid: 0 for nid in node_ids}
    for e in dag.edges:
        outdegree[e.src] = outdegree.get(e.src, 0) + 1

    rem: dict[int, int] = {nid: 0 for nid in node_ids}
    queue = deque(nid for nid, od in outdegree.items() if od == 0)
    tmp_outdeg = dict(outdegree)
    while queue:
        n = queue.popleft()
        for pred in rev.get(n, []):
            rem[pred] = max(rem[pred], rem[n] + 1)
            tmp_outdeg[pred] -= 1
            if tmp_outdeg[pred] == 0:
                queue.append(pred)
    dag.remaining_depth = rem
