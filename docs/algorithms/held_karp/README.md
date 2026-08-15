# Held–Karp

## Design

Input is a fixed start, a fixed goal, a set of intermediate waypoint IDs, and
a directed pairwise cost matrix produced by the routing service. A dynamic
programming state `(visited_mask, last_waypoint)` stores the minimum cost of
reaching the last waypoint after visiting exactly the subset in the mask.
Predecessors reconstruct the selected order.

The method costs `O(k² 2ᵏ)` time and `O(k 2ᵏ)` states. The interactive API
therefore caps it at 10 waypoints. It guarantees the best waypoint order over
the supplied pairwise matrix; segment optimality still depends on the selected
two-point search algorithm.
