# Nearest Neighbor waypoint ordering

`optimize_nearest_neighbor(start_node_id, waypoint_ids, goal_node_id,
pair_costs)` greedily selects the cheapest reachable remaining waypoint and
then connects the final waypoint to the fixed goal.

- Deterministic: equal costs are resolved by a stable node-ID representation.
- Complexity: `O(k²)` for `k` waypoints after the pairwise matrix is built.
- Guarantee: approximate only for more than one waypoint; it may miss the
  globally best ordering.
- Failure: raises `ValueError` when no complete visiting order is reachable.
