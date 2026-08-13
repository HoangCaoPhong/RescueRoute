# Nearest Neighbor

## Design

Input is a fixed start, a fixed goal, a set of intermediate waypoint IDs, and
a directed pairwise cost matrix produced by the routing service. At each step,
the algorithm selects the cheapest reachable unvisited waypoint. Ties use a
stable node-ID representation, so identical inputs always produce the same
order.

Complexity after matrix construction is `O(k²)` for `k` waypoints. The method
is suitable for a quick interactive result but does not guarantee a globally
optimal visiting order when `k > 1`.
