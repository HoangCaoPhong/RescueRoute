# Uniform Cost Search (UCS)

- Owner: Nhân
- Branch: `feature/ucs-search`
- Test folder: `backend/tests/unit/algorithms/graph_search/ucs/`
- Docs folder: `docs/algorithms/ucs/`

## API and guarantees

`solve_ucs(graph, start_node_id, goal_node_id, ...)` is a dedicated public
entry point backed by the shared priority-search implementation with `h = 0`.
It is complete and optimal when all reachable edge costs are non-negative.
The result includes canonical trace events with `node_id`, `g`, `h`, `f`, and
`priority`; an unreachable goal raises `SearchFailure` with its partial trace.
