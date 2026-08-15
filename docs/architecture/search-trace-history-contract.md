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

Priority-based algorithms put structured entries in `frontier`: A* records
`node_id`, `g`, `h`, `f`, and `priority`; UCS records the same shape with
`h = 0`; Dijkstra uses the same shape with accumulated distance. Hill Climbing
records candidate `h`, `priority`, and a `selected` flag. BFS and DFS use node
IDs because their frontiers have no cost priority.

The legacy fields are retained so existing algorithm tests and consumers remain
compatible. `build_search_trace()` prefers the canonical events and normalizes
all frontier entries to objects for the API response.

Each canonical history event keeps at most 250 frontier entries so wide
searches cannot create quadratic memory growth. Its `frontier_size` reports the
full size and `frontier_truncated` records when the snapshot was capped. The API
adapter exposes both fields without changing existing field meanings.

## API and UI behavior

Successful and unsuccessful searches return `search_trace` whenever a trace is
available. It contains `visited_order`, ordered `steps`, the frontier kind, and
coordinates for every node referenced by the trace. The dashboard stores this
one response and uses its local timer only to monitor/play back the history; it
does not rerun a search or request one step at a time.

Algorithms return trace data in memory. They never write JSON files. Optional
offline export is provided by `backend.app.services.trace_exporter`; generated
files live under the ignored `output/traces/` directory by default.
