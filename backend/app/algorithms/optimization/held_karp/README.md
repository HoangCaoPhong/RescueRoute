# Held–Karp waypoint ordering

`optimize_held_karp(start_node_id, waypoint_ids, goal_node_id, pair_costs)`
uses subset dynamic programming with fixed start and goal nodes.

- Complexity: `O(k² 2ᵏ)` time and `O(k 2ᵏ)` states for `k` waypoints.
- Limit: at most 10 waypoints in the interactive API.
- Guarantee: globally optimal waypoint order over the supplied pairwise cost
  matrix; the guarantee for each route segment still belongs to its selected
  graph-search algorithm.
- Failure: raises `ValueError` when no complete visiting order is reachable.
