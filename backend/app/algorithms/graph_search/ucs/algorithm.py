"""Uniform Cost Search using the shared priority-search implementation."""

from typing import Any

from backend.app.algorithms.graph_search.astar import solve_astar
from backend.app.algorithms.graph_search.utils import EdgeCost, NodeId


def solve_ucs(
    graph: Any,
    start_node_id: NodeId,
    goal_node_id: NodeId,
    cost_profile: Any = None,
    edge_cost: EdgeCost | None = None,
) -> dict[str, Any]:
    """Find a minimum-cost route for graphs with non-negative edge costs."""

    result = solve_astar(
        graph,
        start_node_id,
        goal_node_id,
        heuristic=None,
        cost_profile=cost_profile,
        edge_cost=edge_cost,
    )
    result["explanation_data"] = {
        "algorithm": "UCS",
        "optimality": "minimum_cost",
        "message": (
            "Uniform Cost Search expands the lowest accumulated cost first and "
            "is optimal when every edge cost is non-negative."
        ),
    }
    result["is_optimal"] = True
    return result
