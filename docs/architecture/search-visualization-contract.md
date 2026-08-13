# Search Visualization Contract

## Decision

The backend completes a route search before responding. A successful
`POST /api/v1/route` response includes the final route and the full,
deterministic search history in the same JSON payload.

## Response fields used by the dashboard

- `path_nodes` and `path_coords`: the final route to draw.
- `search_trace.visited_order`: the order in which nodes were expanded.
- `search_trace.steps`: the current node and frontier snapshot for every step.
- `search_trace.node_coords`: coordinates for every node referenced by the
  trace, so playback needs no per-step map or API lookup.

This contract is shared by BFS, DFS, UCS, A*, Dijkstra, and Hill Climbing. The frontend owns
only presentation: it stores the response and replays `search_trace.steps` with
its local timer. Playback must never rerun the search algorithm or request a
new trace from the backend.
