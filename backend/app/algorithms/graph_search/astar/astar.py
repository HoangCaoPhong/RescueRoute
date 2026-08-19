"""Deterministic A* search over the project's shared graph abstraction."""

from __future__ import annotations

from collections.abc import Callable
from heapq import heappop, heappush, nsmallest
from itertools import count
from math import isfinite
from time import perf_counter
from typing import Any

from backend.app.algorithms.graph_search.trace_history import (
    SearchFailure,
    SearchTraceHistory,
)
from backend.app.algorithms.graph_search.utils import (
    EdgeCost,
    NodeId,
    calculate_path_metrics,
    get_neighbors,
    has_node,
    reconstruct_path,
    resolve_edge_cost,
)

Heuristic = Callable[[NodeId, NodeId], float]


def solve_astar(
    graph: Any,
    start_node_id: NodeId,
    goal_node_id: NodeId,
    heuristic: Heuristic | None = None,
    cost_profile: Any = None,
    edge_cost: EdgeCost | None = None,
    *,
    heuristic_is_admissible: bool = False,
) -> dict[str, Any]:
    """Find a minimum-cost route with A*.

    ``heuristic`` must return a cost lower bound from its first node to the
    goal. When omitted, A* becomes Uniform Cost Search and remains optimal.
    Callers should set ``heuristic_is_admissible`` only when that property is
    guaranteed for their heuristic and cost profile.
    """
    started_at = perf_counter()
    if not has_node(graph, start_node_id) or not has_node(graph, goal_node_id):
        raise ValueError(
            f"Start node '{start_node_id}' or goal node '{goal_node_id}' does not exist."
        )

    heuristic_fn = heuristic or (lambda _node, _goal: 0.0)

    def estimate(node_id: NodeId) -> float:
        value = float(heuristic_fn(node_id, goal_node_id))
        if not isfinite(value) or value < 0:
            raise ValueError("Heuristic values must be finite and non-negative.")
        return value

    sequence = count()
    g_score: dict[NodeId, float] = {start_node_id: 0.0}
    parent: dict[NodeId, NodeId | None] = {start_node_id: None}
    open_heap: list[tuple[float, float, int, NodeId]] = []
    heappush(open_heap, (estimate(start_node_id), 0.0, next(sequence), start_node_id))
    expanded_at_cost: dict[NodeId, float] = {}
    trace_history = SearchTraceHistory()

    while open_heap:
        current_f, current_cost, _order, current = heappop(open_heap)
        if current_cost != g_score.get(current):
            continue
        if current_cost >= expanded_at_cost.get(current, float("inf")):
            continue

        if trace_history.explored_nodes < 5000:
            remaining_frontier = _active_frontier(
                open_heap,
                g_score,
                expanded_at_cost,
                estimate,
                max_items=24,
            )
            current_item = _frontier_item(
                current,
                current_cost,
                estimate(current),
                current_f,
            )
            trace_history.record_expansion(
                current,
                [current_item, *remaining_frontier],
            )
        else:
            trace_history.record_expansion(current, [])
        expanded_at_cost[current] = current_cost

        if current == goal_node_id:
            path = reconstruct_path(parent, goal_node_id)
            distance, estimated_time, total_cost = calculate_path_metrics(
                graph, path, cost_profile, edge_cost
            )
            optimal = heuristic is None or heuristic_is_admissible
            trace_fields = trace_history.as_result_fields()
            return {
                "found": True,
                "path": path,
                **trace_fields,
                "total_distance": distance,
                "estimated_time": estimated_time,
                "total_cost": total_cost,
                "explored_nodes": trace_history.explored_nodes,
                "processing_time_ms": (perf_counter() - started_at) * 1000.0,
                "is_optimal": optimal,
                "explanation_data": {
                    "algorithm": "A*",
                    "optimality": (
                        "minimum_cost_with_admissible_heuristic"
                        if optimal
                        else "depends_on_heuristic"
                    ),
                    "message": (
                        "A* guarantees a minimum-cost route when edge costs are "
                        "non-negative and the heuristic is admissible."
                    ),
                },
            }

        for neighbor in get_neighbors(graph, current):
            tentative_cost = current_cost + resolve_edge_cost(
                graph, current, neighbor, cost_profile, edge_cost
            )
            if tentative_cost >= g_score.get(neighbor, float("inf")):
                continue
            g_score[neighbor] = tentative_cost
            parent[neighbor] = current
            heappush(
                open_heap,
                (
                    tentative_cost + estimate(neighbor),
                    tentative_cost,
                    next(sequence),
                    neighbor,
                ),
            )

    message = f"No route found from '{start_node_id}' to '{goal_node_id}'."
    trace_fields = trace_history.as_result_fields()
    raise SearchFailure(
        message,
        {
            "found": False,
            "path": [],
            **trace_fields,
            "explored_nodes": trace_history.explored_nodes,
            "processing_time_ms": (perf_counter() - started_at) * 1000.0,
            "message": message,
        },
    )


def _active_frontier(
    heap: list[tuple[float, float, int, NodeId]],
    g_score: dict[NodeId, float],
    expanded_at_cost: dict[NodeId, float],
    estimate: Callable[[NodeId], float],
    max_items: int = 24,
) -> list[dict[str, Any]]:

    """Return the effective heap frontier in deterministic priority order."""
    frontier: list[dict[str, Any]] = []
    seen: set[NodeId] = set()
    candidates = nsmallest(max_items * 3, heap) if len(heap) > max_items * 3 else sorted(heap)
    for _f_score, cost, _order, node_id in candidates:
        if node_id in seen or cost != g_score.get(node_id):
            continue
        if cost >= expanded_at_cost.get(node_id, float("inf")):
            continue
        seen.add(node_id)
        heuristic = estimate(node_id)
        frontier.append(_frontier_item(node_id, cost, heuristic, cost + heuristic))
        if len(frontier) >= max_items:
            break
    return frontier



def _frontier_item(
    node_id: NodeId,
    cost: float,
    heuristic: float,
    priority: float,
) -> dict[str, Any]:
    """Return the canonical priority-frontier representation."""

    return {
        "node_id": node_id,
        "g": round(cost, 6),
        "h": round(heuristic, 6),
        "f": round(priority, 6),
        "priority": round(priority, 6),
    }
