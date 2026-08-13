# Dijkstra's Algorithm

- Owner: Hòa
- Branch: `feature/dijkstra-search`
- Test folder: `backend/tests/unit/algorithms/graph_search/dijkstra/`
- Docs folder: `docs/algorithms/dijkstra/`

## API and guarantees

`solve_dijkstra(graph, start_node_id, goal_node_id, edge_cost=...)` is a
dedicated public entry point backed by the shared priority-search
implementation with `h = 0`. It is complete and optimal for the selected
non-negative edge weight. The default demo service supplies road distance as
that weight. Trace events expose each node's accumulated cost and an
unreachable goal preserves the partial trace in `SearchFailure`.
