"""Deterministic Hill Climbing for route construction."""

from __future__ import annotations

from collections.abc import Callable
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
)

Heuristic = Callable[[NodeId, NodeId], float]


def solve_hill_climbing(
    graph: Any,
    start_node_id: NodeId,
    goal_node_id: NodeId,
    heuristic: Heuristic,
    cost_profile: Any = None,
    edge_cost: EdgeCost | None = None,
    *,
    allow_sideways: bool = False,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """Build a route by repeatedly choosing the best heuristic neighbor.

    Smaller heuristic values are better. The algorithm is deterministic and
    never revisits a node. It raises ``ValueError`` when a local optimum,
    plateau, cycle, or the configured step limit prevents reaching the goal.
    """
    started_at = perf_counter()
    if not has_node(graph, start_node_id) or not has_node(graph, goal_node_id):
        raise ValueError(
            f"Start node '{start_node_id}' or goal node '{goal_node_id}' does not exist."
        )
    if max_steps is not None and max_steps < 0:
        raise ValueError("max_steps must be non-negative or None.")

    def estimate(node_id: NodeId) -> float:
        value = float(heuristic(node_id, goal_node_id))
        if not isfinite(value) or value < 0:
            raise ValueError("Heuristic values must be finite and non-negative.")
        return value

    current = start_node_id
    current_estimate = estimate(current)
    path: list[NodeId] = [current]
    visited = {current}
    trace_history = SearchTraceHistory()
    frontier_steps: list[list[NodeId]] = []
    heuristic_steps: list[dict[str, Any]] = []

    while True:
        if current == goal_node_id:
            trace_history.record_expansion(current, [])
            distance, estimated_time, total_cost = calculate_path_metrics(
                graph, path, cost_profile, edge_cost
            )
            trace_fields = trace_history.as_result_fields()
            trace_fields["frontier_steps"] = frontier_steps
            return {
                "found": True,
                "path": path,
                **trace_fields,
                "heuristic_steps": heuristic_steps,
                "total_distance": distance,
                "estimated_time": estimated_time,
                "total_cost": total_cost,
                "explored_nodes": trace_history.explored_nodes,
                "processing_time_ms": (perf_counter() - started_at) * 1000.0,
                "is_optimal": False,
                "explanation_data": {
                    "algorithm": "Hill Climbing",
                    "optimality": "local_search_no_global_guarantee",
                    "message": (
                        "Hill Climbing follows the locally best heuristic value; "
                        "it is fast but is neither complete nor globally optimal."
                    ),
                },
            }

        if max_steps is not None and len(path) - 1 >= max_steps:
            trace_history.record_expansion(current, [])
            _raise_search_failure(
                trace_history,
                frontier_steps,
                started_at,
                f"Hill Climbing did not reach '{goal_node_id}' within {max_steps} steps.",
            )

        candidates = [node for node in get_neighbors(graph, current) if node not in visited]
        ranked = sorted((estimate(node), repr(node), node) for node in candidates)
        frontier_steps.append([node for _score, _key, node in ranked])
        if not ranked:
            trace_history.record_expansion(current, [])
            _raise_search_failure(
                trace_history,
                frontier_steps,
                started_at,
                f"Hill Climbing reached a dead end at '{current}' before '{goal_node_id}'.",
            )

        next_estimate, _key, next_node = ranked[0]
        improves = next_estimate < current_estimate
        sideways = allow_sideways and next_estimate == current_estimate
        trace_history.record_expansion(
            current,
            [
                {
                    "node_id": node,
                    "h": round(score, 6),
                    "priority": round(score, 6),
                    "selected": bool(node == next_node and (improves or sideways)),
                }
                for score, _key, node in ranked
            ],
        )

        if not improves and not sideways:
            _raise_search_failure(
                trace_history,
                frontier_steps,
                started_at,
                f"Hill Climbing reached a local optimum at '{current}' before "
                f"'{goal_node_id}'.",
            )

        heuristic_steps.append(
            {
                "current": current,
                "current_heuristic": current_estimate,
                "selected": next_node,
                "selected_heuristic": next_estimate,
            }
        )
        current = next_node
        current_estimate = next_estimate
        path.append(current)
        visited.add(current)


def _raise_search_failure(
    trace_history: SearchTraceHistory,
    frontier_steps: list[list[NodeId]],
    started_at: float,
    message: str,
) -> None:
    trace_fields = trace_history.as_result_fields()
    trace_fields["frontier_steps"] = frontier_steps
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
