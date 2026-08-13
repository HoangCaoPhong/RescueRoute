# A\* Search

- Owner: Phong
- Branch: `feature/astar-search`
- Test folder: `backend/tests/unit/algorithms/graph_search/astar/`
- Docs folder: `docs/algorithms/astar/`

## API

`solve_astar(graph, start_node_id, goal_node_id, heuristic=None, ...)` uses a
priority queue ordered by `f(n) = g(n) + h(n)`. The heuristic and optional
edge-cost callback use the same unit as the shared cost profile. If no
heuristic is supplied, the function behaves as Uniform Cost Search.

The implementation supports directed adjacency dictionaries and the shared
Graph abstraction. It returns the route, expansion order, frontier snapshots,
route metrics, timing, and structured optimality explanation.

## Guarantees

- Complete on a finite graph with non-negative finite edge costs.
- Optimal when `h` is admissible; a consistent heuristic also avoids repeated
  expansion. Set `heuristic_is_admissible=True` only after verifying that
  property for the active cost profile.
- Deterministic for the same graph iteration order, inputs, and callbacks.
- Raises `ValueError` for missing nodes, invalid costs/heuristics, or no route.
