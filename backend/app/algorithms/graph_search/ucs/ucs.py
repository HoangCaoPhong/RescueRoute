"""Uniform Cost Search — native implementation with shared graph/trace contracts.

UCS expands nodes in order of their accumulated path cost (g-score) with h = 0.
It is complete and optimal when all reachable edge costs are non-negative.
The result shape is identical to A* so that ``routing_service`` handles both
algorithms through the same ``build_success_response`` path.
"""

from __future__ import annotations

from heapq import heappop, heappush, nsmallest
from itertools import count
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



def solve_ucs(
    graph: Any,
    start_node_id: NodeId,
    goal_node_id: NodeId,
    cost_profile: Any = None,
    edge_cost: EdgeCost | None = None,
) -> dict[str, Any]:
    """Find a minimum-cost route using Uniform Cost Search.

    Expands nodes strictly in order of accumulated path cost (h = 0 always).
    Raises ``SearchFailure`` — with the partial trace attached — when the goal
    is unreachable.  All edge costs must be finite and non-negative.
    """
    started_at = perf_counter()

    if not has_node(graph, start_node_id) or not has_node(graph, goal_node_id):
        raise ValueError(
            f"Start node '{start_node_id}' or goal node '{goal_node_id}' does not exist."
        )

    sequence = count()
    g_score: dict[NodeId, float] = {start_node_id: 0.0}
    parent: dict[NodeId, NodeId | None] = {start_node_id: None}

    # Heap entries: (g, tie-breaker, node_id)
    open_heap: list[tuple[float, int, NodeId]] = []
    heappush(open_heap, (0.0, next(sequence), start_node_id))

    expanded_at_cost: dict[NodeId, float] = {}
    trace_history = SearchTraceHistory()
    legacy_frontier_steps: list[list[NodeId]] = []

    while open_heap:
        current_g, _order, current = heappop(open_heap)

        # Skip stale heap entries (lazy deletion)
        if current_g != g_score.get(current):
            continue
        if current_g >= expanded_at_cost.get(current, float("inf")):
            continue

        # Build canonical frontier snapshot before expansion
        if len(legacy_frontier_steps) < 5000:
            remaining_frontier = _active_frontier(
                open_heap,
                g_score,
                expanded_at_cost,
                max_items=24,
            )
            current_item = _frontier_item(current, current_g)
            trace_history.record_expansion(
                current,
                [current_item, *remaining_frontier],
            )
            legacy_frontier_steps.append(
                [current, *[item["node_id"] for item in remaining_frontier]]
            )
        else:
            trace_history.record_expansion(current, [])
            legacy_frontier_steps.append([current])
        expanded_at_cost[current] = current_g


        if current == goal_node_id:
            path = reconstruct_path(parent, goal_node_id)
            distance, estimated_time, total_cost = calculate_path_metrics(
                graph, path, cost_profile, edge_cost
            )
            trace_fields = trace_history.as_result_fields()
            trace_fields["frontier_steps"] = legacy_frontier_steps
            return {
                "found": True,
                "path": path,
                **trace_fields,
                "total_distance": distance,
                "estimated_time": estimated_time,
                "total_cost": total_cost,
                "explored_nodes": trace_history.explored_nodes,
                "processing_time_ms": (perf_counter() - started_at) * 1000.0,
                "is_optimal": True,
                "explanation_data": {
                    "algorithm": "UCS",
                    "optimality": "minimum_cost",
                    "message": (
                        "Uniform Cost Search expands the lowest accumulated cost "
                        "first and is optimal when every edge cost is non-negative."
                    ),
                },
            }

        for neighbor in get_neighbors(graph, current):
            tentative_g = current_g + resolve_edge_cost(
                graph, current, neighbor, cost_profile, edge_cost
            )
            if tentative_g >= g_score.get(neighbor, float("inf")):
                continue
            g_score[neighbor] = tentative_g
            parent[neighbor] = current
            heappush(open_heap, (tentative_g, next(sequence), neighbor))

    message = f"No route found from '{start_node_id}' to '{goal_node_id}'."
    trace_fields = trace_history.as_result_fields()
    trace_fields["frontier_steps"] = legacy_frontier_steps
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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _active_frontier(
    heap: list[tuple[float, int, NodeId]],
    g_score: dict[NodeId, float],
    expanded_at_cost: dict[NodeId, float],
    max_items: int = 24,
) -> list[dict[str, Any]]:

    """Return the effective heap frontier in deterministic cost order."""
    frontier: list[dict[str, Any]] = []
    seen: set[NodeId] = set()
    candidates = nsmallest(max_items * 3, heap) if len(heap) > max_items * 3 else sorted(heap)
    for cost, _order, node_id in candidates:
        if node_id in seen or cost != g_score.get(node_id):
            continue
        if cost >= expanded_at_cost.get(node_id, float("inf")):
            continue
        seen.add(node_id)
        frontier.append(_frontier_item(node_id, cost))
        if len(frontier) >= max_items:
            break
    return frontier



def _frontier_item(node_id: NodeId, cost: float) -> dict[str, Any]:
    """Return the canonical priority-frontier item for UCS (h = 0, f = g)."""
    return {
        "node_id": node_id,
        "g": round(cost, 6),
        "h": 0.0,
        "f": round(cost, 6),
        "priority": round(cost, 6),
    }
