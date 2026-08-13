"""Held–Karp dynamic programming for small fixed-start/fixed-goal routes."""

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any


MAX_HELD_KARP_WAYPOINTS = 10


def optimize_held_karp(
    start_node_id: Any,
    waypoint_ids: Sequence[Any],
    goal_node_id: Any,
    pair_costs: Mapping[tuple[Any, Any], float],
) -> dict[str, Any]:
    """Return the optimal waypoint order under the supplied pairwise costs."""

    waypoints = list(dict.fromkeys(waypoint_ids))
    if len(waypoints) > MAX_HELD_KARP_WAYPOINTS:
        raise ValueError(
            f"Held-Karp supports at most {MAX_HELD_KARP_WAYPOINTS} waypoints."
        )
    if not waypoints:
        direct_cost = _cost(pair_costs, start_node_id, goal_node_id)
        if not isfinite(direct_cost):
            raise ValueError(f"No route from '{start_node_id}' to '{goal_node_id}'.")
        return {
            "visiting_order": [start_node_id, goal_node_id],
            "objective_cost": direct_cost,
            "is_optimal": True,
            "method": "held_karp",
        }

    # (visited_mask, last_index) -> (cost, predecessor_index)
    dp: dict[tuple[int, int], tuple[float, int | None]] = {}
    for index, waypoint in enumerate(waypoints):
        initial_cost = _cost(pair_costs, start_node_id, waypoint)
        if isfinite(initial_cost):
            dp[(1 << index, index)] = (initial_cost, None)

    for mask in range(1, 1 << len(waypoints)):
        for last in range(len(waypoints)):
            state = dp.get((mask, last))
            if state is None:
                continue
            current_cost, _predecessor = state
            for nxt in range(len(waypoints)):
                if mask & (1 << nxt):
                    continue
                new_mask = mask | (1 << nxt)
                transition_cost = _cost(
                    pair_costs,
                    waypoints[last],
                    waypoints[nxt],
                )
                if not isfinite(transition_cost):
                    continue
                candidate = current_cost + transition_cost
                existing = dp.get((new_mask, nxt))
                if existing is None or candidate < existing[0]:
                    dp[(new_mask, nxt)] = (candidate, last)

    full_mask = (1 << len(waypoints)) - 1
    final_candidates = [
        (
            dp[(full_mask, last)][0]
            + _cost(pair_costs, waypoints[last], goal_node_id),
            last,
        )
        for last in range(len(waypoints))
        if (full_mask, last) in dp
    ]
    final_candidates = [item for item in final_candidates if isfinite(item[0])]
    if not final_candidates:
        raise ValueError("No route can visit every waypoint and reach the goal.")
    final_cost, final_last = min(final_candidates)

    reverse_indices = []
    mask = full_mask
    last: int | None = final_last
    while last is not None:
        reverse_indices.append(last)
        _cost_value, predecessor = dp[(mask, last)]
        mask ^= 1 << last
        last = predecessor
    ordered_waypoints = [waypoints[index] for index in reversed(reverse_indices)]
    return {
        "visiting_order": [start_node_id, *ordered_waypoints, goal_node_id],
        "objective_cost": final_cost,
        "is_optimal": True,
        "method": "held_karp",
    }


def _cost(
    pair_costs: Mapping[tuple[Any, Any], float],
    source: Any,
    target: Any,
) -> float:
    value = float(pair_costs.get((source, target), float("inf")))
    if value < 0:
        raise ValueError("Pair costs must be non-negative.")
    return value
