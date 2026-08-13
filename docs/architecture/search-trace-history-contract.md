# Search Trace History Contract

## Decision

Every graph-search implementation records a trace with the shared
`SearchTraceHistory` template before expanding each node. The template is
framework-free and lives under `backend/app/algorithms/graph_search/`, so it
can be used by BFS, DFS, UCS, A*, Dijkstra, and future search algorithms.

## Algorithm result compatibility

`SearchTraceHistory.as_result_fields()` provides both existing result fields
and the canonical event stream:

- `visited_order`: nodes expanded in deterministic order.
- `frontier_steps`: the frontier snapshot corresponding to each expansion.
- `trace_history.version`: currently `1.0`.
- `trace_history.events`: `{step, current_node, frontier}` for every expansion.

The legacy fields are retained so existing algorithm tests and consumers remain
compatible. `build_search_trace()` prefers the canonical events and normalizes
all frontier entries to objects for the API response.

## API and UI behavior

Successful and unsuccessful searches return `search_trace` whenever a trace is
available. It contains `visited_order`, ordered `steps`, the frontier kind, and
coordinates for every node referenced by the trace. The dashboard stores this
one response and uses its local timer only to monitor/play back the history; it
does not rerun a search or request one step at a time.
