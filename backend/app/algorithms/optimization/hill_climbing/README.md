# Hill Climbing

- Owner: Phong
- Branch: `feature/hill-climbing`
- Test folder: `backend/tests/unit/algorithms/optimization/hill_climbing/`
- Docs folder: `docs/algorithms/hill_climbing/`

## API

`solve_hill_climbing(graph, start_node_id, goal_node_id, heuristic, ...)`
constructs a route by moving to the unvisited neighbor with the smallest
heuristic value. Equal candidates are ordered deterministically. Sideways
moves and a maximum step count are explicit options.

The result follows the common route-search shape and adds `heuristic_steps` so
the UI can explain each local decision.

## Guarantees and limitations

- Fast and deterministic, but neither complete nor globally optimal.
- Can stop at a local optimum, plateau, dead end, or step limit; these cases
  raise `ValueError` with the stopping reason.
- Does not mutate the graph and never revisits a node.
- The heuristic must be finite, non-negative, and expressed consistently for
  the caller's routing objective.
