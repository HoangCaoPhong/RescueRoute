from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence
from math import isfinite
from typing import Any


NodeId = Hashable
EdgeCost = Callable[[Any, NodeId, NodeId, Any], float]


def reconstruct_path(parent, goal_node_id):
    """Reconstruct path from start node to goal node."""
    path = []
    current = goal_node_id

    while current is not None:
        path.append(current)
        current = parent[current]

    return path[::-1]


def get_neighbors(graph, node_id):
    """Get neighbors in deterministic order."""

    if isinstance(graph, dict):
        raw_neighbors = graph.get(node_id, [])
        if isinstance(raw_neighbors, dict):
            neighbors = raw_neighbors.keys()
        else:
            neighbors = raw_neighbors
        return sorted(list(neighbors))

    # Common Graph abstraction
    edges = graph.get_neighbors(node_id)
    return sorted([edge.v for edge in edges])


def has_node(graph: Any, node_id: NodeId) -> bool:
    """Return whether *node_id* exists without changing the graph."""
    if isinstance(graph, Mapping):
        return node_id in graph
    return bool(graph.has_node(node_id))


def get_edge_data(graph: Any, source: NodeId, target: NodeId) -> Any:
    """Read edge data from the supported graph abstractions."""
    if isinstance(graph, Mapping):
        neighbors = graph[source]
        if isinstance(neighbors, Mapping):
            return neighbors[target]
        return 1.0

    if hasattr(graph, "get_edge"):
        return graph.get_edge(source, target)

    for edge in graph.get_neighbors(source):
        if edge.v == target:
            return edge
    raise KeyError(f"Edge from '{source}' to '{target}' does not exist.")


def resolve_edge_cost(
    graph: Any,
    source: NodeId,
    target: NodeId,
    cost_profile: Any = None,
    edge_cost: EdgeCost | None = None,
) -> float:
    """Resolve one non-negative edge cost through the shared graph/caller API."""
    if edge_cost is not None:
        value = edge_cost(graph, source, target, cost_profile)
    elif hasattr(graph, "calculate_edge_cost"):
        value = graph.calculate_edge_cost(source, target, cost_profile)
    else:
        edge = get_edge_data(graph, source, target)
        if isinstance(edge, (int, float)):
            value = edge
        elif isinstance(edge, Mapping):
            value = next(
                (edge[key] for key in ("total_cost", "cost", "weight") if key in edge),
                1.0,
            )
        elif isinstance(edge, Sequence) and not isinstance(edge, (str, bytes)):
            value = edge[0] if edge else 1.0
        elif hasattr(edge, "cost"):
            value = edge.cost
        else:
            value = 1.0

    cost = float(value)
    if not isfinite(cost) or cost < 0:
        raise ValueError(
            f"Edge cost from '{source}' to '{target}' must be finite and non-negative."
        )
    return cost


def calculate_path_metrics(
    graph: Any,
    path: list[NodeId],
    cost_profile: Any = None,
    edge_cost: EdgeCost | None = None,
) -> tuple[float | None, float | None, float]:
    """Calculate route metrics while deferring to the graph contract when present."""
    if hasattr(graph, "calculate_path_metrics"):
        distance, estimated_time, total_cost = graph.calculate_path_metrics(
            path, cost_profile
        )
        return distance, estimated_time, float(total_cost)

    total_cost = 0.0
    total_distance = 0.0
    has_distance = True
    estimated_time = 0.0
    has_time = True

    for source, target in zip(path, path[1:]):
        total_cost += resolve_edge_cost(
            graph, source, target, cost_profile, edge_cost
        )
        edge = get_edge_data(graph, source, target)

        if isinstance(edge, Mapping) and "distance" in edge:
            total_distance += float(edge["distance"])
        elif (
            isinstance(edge, Sequence)
            and not isinstance(edge, (str, bytes))
            and len(edge) > 2
        ):
            total_distance += float(edge[2])
        else:
            has_distance = False

        if isinstance(edge, Mapping) and "estimated_time" in edge:
            estimated_time += float(edge["estimated_time"])
        elif isinstance(edge, Mapping) and "time" in edge:
            estimated_time += float(edge["time"])
        else:
            has_time = False

    return (
        total_distance if has_distance else None,
        estimated_time if has_time else None,
        total_cost,
    )
