"""Dijkstra shortest-path search over the shared graph abstraction."""

from typing import Any

from backend.app.algorithms.graph_search.astar import solve_astar
from backend.app.algorithms.graph_search.utils import EdgeCost, NodeId


def solve_dijkstra(
    graph: Any,
    start_node_id: NodeId,
    goal_node_id: NodeId,
    cost_profile: Any = None,
    edge_cost: EdgeCost | None = None,
) -> dict[str, Any]:
    """Find a shortest route using the supplied non-negative edge weight."""

    result = solve_astar(
        graph,
        start_node_id,
        goal_node_id,
        heuristic=None,
        cost_profile=cost_profile,
        edge_cost=edge_cost,
    )
    result["explanation_data"] = {
        "algorithm": "Dijkstra",
        "optimality": "minimum_weight",
        "message": (
            "Dijkstra expands the lowest accumulated weight first and is "
            "optimal when every selected edge weight is non-negative."
        ),
    }
    result["is_optimal"] = True
    return result
