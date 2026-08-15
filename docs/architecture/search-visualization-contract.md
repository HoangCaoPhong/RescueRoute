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

During playback, the dashboard must not draw the final route upfront. It reveals
the final-route prefix only as each corresponding path node is expanded. When a
trace coordinate is absent, the dashboard recovers it from the existing edge
data before playback; an unrecoverable position creates a gap in the polyline
rather than shifting later node coordinates onto the wrong path node.

The dashboard may offer presentation modes without changing the trace contract.
Its default route-focused mode keeps the marker and camera on the final route
while displaying the frontier; a full-trace mode displays all visited and
frontier nodes from the same saved search history.
