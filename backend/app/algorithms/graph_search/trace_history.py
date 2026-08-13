"""Reusable, framework-free trace history for graph-search algorithms."""

from copy import deepcopy
from typing import Any, Dict, Iterable, List


TRACE_HISTORY_VERSION = "1.0"
MAX_FRONTIER_ITEMS = 250


class SearchFailure(ValueError):
    """A failed search that still exposes its completed trace fields."""

    def __init__(self, message: str, result: Dict[str, Any]) -> None:
        super().__init__(message)
        self.result = result


class SearchTraceHistory:
    """Record deterministic search snapshots in the shared visualization shape.

    The frontier supplied to :meth:`record_expansion` is the state immediately
    before ``current_node`` is expanded. Nodes may be IDs (BFS/DFS) or objects
    with costs (UCS, A*, Dijkstra). This keeps every algorithm compatible with
    the same frontend trace adapter without coupling algorithm code to FastAPI.
    """

    def __init__(self) -> None:
        self._visited_order: List[Any] = []
        self._events: List[Dict[str, Any]] = []

    def record_expansion(self, current_node: Any, frontier: Iterable[Any]) -> None:
        """Save one immutable snapshot before expanding ``current_node``."""

        frontier_items = list(frontier)
        frontier_snapshot = deepcopy(frontier_items[:MAX_FRONTIER_ITEMS])
        self._visited_order.append(current_node)
        self._events.append(
            {
                "step": len(self._events) + 1,
                "current_node": current_node,
                "frontier": frontier_snapshot,
                "frontier_size": len(frontier_items),
                "frontier_truncated": len(frontier_items) > MAX_FRONTIER_ITEMS,
            }
        )

    @property
    def explored_nodes(self) -> int:
        """Return the number of recorded node expansions."""

        return len(self._visited_order)

    def as_result_fields(self) -> Dict[str, Any]:
        """Return fields shared by algorithm results and the trace adapter.

        ``visited_order`` and ``frontier_steps`` remain available for existing
        algorithm consumers. ``trace_history.events`` is the canonical event
        stream for new consumers.
        """

        events = deepcopy(self._events)
        return {
            "visited_order": list(self._visited_order),
            "frontier_steps": [
                event["frontier"]
                for event in events
            ],
            "trace_history": {
                "version": TRACE_HISTORY_VERSION,
                "events": events,
            },
        }
