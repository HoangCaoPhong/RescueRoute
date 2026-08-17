"""Deterministic Nearest Neighbor ordering for fixed-start/fixed-goal routes."""

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from backend.app.algorithms.optimization.utils import get_pairwise_cost


def optimize_nearest_neighbor(
    start_node_id: Any,
    waypoint_ids: Sequence[Any],
    goal_node_id: Any,
    pair_costs: Mapping[tuple[Any, Any], float],
) -> dict[str, Any]:
    """Return a deterministic approximate visiting order."""

    remaining = list(dict.fromkeys(waypoint_ids))
    order = [start_node_id]
    current = start_node_id
    total_cost = 0.0

    while remaining:
        candidates = [
            (get_pairwise_cost(pair_costs, current, node_id), repr(node_id), node_id)
            for node_id in remaining
        ]
        cost, _key, selected = min(candidates)
        if not isfinite(cost):
            raise ValueError(
                f"No remaining waypoint is reachable from '{current}'."
            )
        total_cost += cost
        order.append(selected)
        remaining.remove(selected)
        current = selected

    final_cost = get_pairwise_cost(pair_costs, current, goal_node_id)
    if not isfinite(final_cost):
        raise ValueError(f"No route from '{current}' to '{goal_node_id}'.")
    total_cost += final_cost
    order.append(goal_node_id)
    return {
        "visiting_order": order,
        "objective_cost": total_cost,
        "is_optimal": len(waypoint_ids) <= 1,
        "method": "nearest_neighbor",
    }

