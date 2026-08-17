import pytest

from backend.app.algorithms.graph_search.trace_history import SearchFailure
from backend.app.algorithms.graph_search.ucs import solve_ucs


GRAPH = {
    "S": {"A": 2.0, "B": 1.0},
    "A": {"G": 2.0},
    "B": {"G": 10.0},
    "G": {},
}


def test_ucs_returns_optimal_cost_and_canonical_priority_trace():
    result = solve_ucs(GRAPH, "S", "G")

    assert result["path"] == ["S", "A", "G"]
    assert result["total_cost"] == 4.0
    assert result["is_optimal"] is True
    first = result["trace_history"]["events"][0]["frontier"][0]
    assert first == {"node_id": "S", "g": 0.0, "h": 0.0, "f": 0.0, "priority": 0.0}


def test_ucs_preserves_partial_trace_when_no_route_exists():
    with pytest.raises(SearchFailure) as caught:
        solve_ucs({"S": {}, "G": {}}, "S", "G")

    assert caught.value.result["visited_order"] == ["S"]
