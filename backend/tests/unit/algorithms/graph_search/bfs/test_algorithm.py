import pytest
from backend.app.algorithms.graph_search.bfs.bfs import solve_bfs
from backend.tests.fixtures.bfs_graphs import (
    MINIMUM_HOP_GRAPH,
    DIRECTED_GRAPH,
    NO_PATH_GRAPH,
    DUPLICATE_DISCOVERY_GRAPH,
)


def test_bfs_finds_minimum_hop_path():
    result = solve_bfs(
        MINIMUM_HOP_GRAPH,
        "A",
        "D"
    )

    assert result["path"] == ["A", "B", "D"]
    assert result["hop_count"] == 2
    assert result["is_optimal"] is True


def test_bfs_start_equals_goal():
    result = solve_bfs(
        MINIMUM_HOP_GRAPH,
        "A",
        "A"
    )

    assert result["path"] == ["A"]
    assert result["hop_count"] == 0
    assert result["visited_order"] == ["A"]
    assert result["explored_nodes"] == 1


def test_bfs_no_path():
    with pytest.raises(ValueError):
        solve_bfs(
            NO_PATH_GRAPH,
            "A",
            "C"
        )


def test_bfs_respects_directed_graph():
    result = solve_bfs(
        DIRECTED_GRAPH,
        "A",
        "B"
    )

    assert result["path"] == ["A", "B"]
    assert result["hop_count"] == 1

    with pytest.raises(ValueError):
        solve_bfs(
            DIRECTED_GRAPH,
            "B",
            "A"
        )


def test_bfs_does_not_expand_node_twice():
    result = solve_bfs(
        DUPLICATE_DISCOVERY_GRAPH,
        "A",
        "D"
    )

    visited_order = result["visited_order"]

    assert len(visited_order) == len(set(visited_order))
    assert visited_order.count("D") == 1


def test_bfs_frontier_steps():
    result = solve_bfs(
        MINIMUM_HOP_GRAPH,
        "A",
        "D"
    )

    steps = result["frontier_steps"]

    assert steps[0] == ["A"]
    assert steps[1] == ["B", "C"]
    assert steps[2] == ["C", "D"]
    assert steps[-1] == ["D", "E"]


def test_bfs_returns_required_result_fields():
    result = solve_bfs(
        MINIMUM_HOP_GRAPH,
        "A",
        "D"
    )

    required_fields = {
        "path",
        "visited_order",
        "frontier_steps",
        "trace_history",
        "total_distance",
        "estimated_time",
        "total_cost",
        "explored_nodes",
        "processing_time_ms",
        "is_optimal",
        "explanation_data",
        "hop_count",
    }

    assert required_fields.issubset(result.keys())


def test_bfs_trace_history_matches_legacy_trace_fields():
    result = solve_bfs(MINIMUM_HOP_GRAPH, "A", "D")

    events = result["trace_history"]["events"]

    assert [event["current_node"] for event in events] == result["visited_order"]
    assert [event["frontier"] for event in events] == result["frontier_steps"]


def test_bfs_dict_graph_has_no_route_metrics():
    result = solve_bfs(
        MINIMUM_HOP_GRAPH,
        "A",
        "D"
    )

    assert result["total_distance"] is None
    assert result["estimated_time"] is None
    assert result["total_cost"] is None


def test_bfs_processing_time_is_non_negative():
    result = solve_bfs(
        MINIMUM_HOP_GRAPH,
        "A",
        "D"
    )

    assert result["processing_time_ms"] >= 0


def test_bfs_invalid_node():
    with pytest.raises(ValueError):
        solve_bfs(
            MINIMUM_HOP_GRAPH,
            "UNKNOWN_NODE",
            "D"
        )
