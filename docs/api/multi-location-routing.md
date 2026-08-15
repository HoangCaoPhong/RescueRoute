# Multi-location routing API

`POST /api/v1/route/multi-location` optimizes the visiting order of intermediate
locations while keeping the selected start and destination fixed.

## Request

```json
{
  "start_node_id": 100,
  "waypoint_ids": [200, 300, 400],
  "goal_node_id": 900,
  "route_algorithm": "astar",
  "optimization_method": "held_karp",
  "criterion": "cost"
}
```

Supported ordering methods:

- `nearest_neighbor`: deterministic approximation.
- `held_karp`: optimal order over the computed pairwise route-cost matrix,
  limited to 10 waypoints.

Supported criteria are `cost`, `distance`, `hops`, and `time`. The current
dataset has no independent edge-time field, so `time` uses the traffic-aware
composite cost as its ordering proxy.

The response includes `visiting_order`, `ordered_waypoints`, selected
`segments`, merged paths, and aggregate metrics. `order_is_optimal` only
describes the waypoint ordering over the pairwise matrix; route optimality
still depends on the selected route algorithm and heuristic assumptions.

## Errors

The service returns `found: false` with a user-facing `message` when a segment
is unreachable, the optimization method is unsupported, or no order can visit
every waypoint. Requests with more than 10 distinct intermediate waypoints are
rejected before the pairwise routes are evaluated.

```json
{
  "found": false,
  "optimization_method": "held_karp",
  "message": "No route can visit every waypoint and reach the goal."
}
```
