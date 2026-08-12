import pytest
from backend.app.algorithms.graph_search.dfs.dfs import solve_dfs


# Graph with multiple paths for testing DFS
SAMPLE_GRAPH = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["E"],
    "D": [],
    "E": ["D"],
}

DIRECTED_GRAPH = {
    "A": ["B"],
    "B": []
}

NO_PATH_GRAPH = {
    "A": ["B"],
    "B": [],
    "C": []
}

CYCLE_GRAPH = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["D"],
    "D": []
}


def test_dfs_finds_path():
    result = solve_dfs(
        SAMPLE_GRAPH,
        "A",
        "D"
    )

    assert result["path"] == ["A", "B", "D"]
    assert result["is_optimal"] is False


def test_dfs_start_equals_goal():
    result = solve_dfs(
        SAMPLE_GRAPH,
        "A",
        "A"
    )

    assert result["path"] == ["A"]
    assert result["visited_order"] == ["A"]
    assert result["explored_nodes"] == 1


def test_dfs_no_path():
    with pytest.raises(ValueError):
        solve_dfs(
            NO_PATH_GRAPH,
            "A",
            "C"
        )


def test_dfs_respects_directed_graph():
    result = solve_dfs(
        DIRECTED_GRAPH,
        "A",
        "B"
    )

    assert result["path"] == ["A", "B"]

    with pytest.raises(ValueError):
        solve_dfs(
            DIRECTED_GRAPH,
            "B",
            "A"
        )


def test_dfs_does_not_expand_node_twice():
    result = solve_dfs(
        CYCLE_GRAPH,
        "A",
        "D"
    )

    visited_order = result["visited_order"]

    assert len(visited_order) == len(set(visited_order))
    assert visited_order.count("D") == 1


def test_dfs_frontier_steps():
    result = solve_dfs(
        SAMPLE_GRAPH,
        "A",
        "D"
    )

    steps = result["frontier_steps"]

    assert steps[0] == ["A"]
    assert steps[1] == ["C", "B"]
    assert steps[2] == ["C", "D"]


def test_dfs_returns_required_result_fields():
    result = solve_dfs(
        SAMPLE_GRAPH,
        "A",
        "D"
    )

    required_fields = {
        "path",
        "visited_order",
        "frontier_steps",
        "total_distance",
        "estimated_time",
        "total_cost",
        "explored_nodes",
        "processing_time_ms",
        "is_optimal",
        "explanation_data",
    }

    assert required_fields.issubset(result.keys())


def test_dfs_dict_graph_has_no_route_metrics():
    result = solve_dfs(
        SAMPLE_GRAPH,
        "A",
        "D"
    )

    assert result["total_distance"] is None
    assert result["estimated_time"] is None
    assert result["total_cost"] is None


def test_dfs_processing_time_is_non_negative():
    result = solve_dfs(
        SAMPLE_GRAPH,
        "A",
        "D"
    )

    assert result["processing_time_ms"] >= 0


def test_dfs_invalid_node():
    with pytest.raises(ValueError):
        solve_dfs(
            SAMPLE_GRAPH,
            "UNKNOWN_NODE",
            "D"
        )


def test_dfs_reconstructs_actual_traversed_path():
    # Graph where node B can be reached from A directly or via C.
    # DFS explores branch C -> B -> D.
    graph = {
        "A": ["B", "C"],
        "C": ["B"],
        "B": ["D"],
        "D": []
    }
    result = solve_dfs(graph, "A", "D")
    path = result["path"]
    # Verify each edge in reconstructed path actually exists in graph
    for u, v in zip(path[:-1], path[1:]):
        assert v in graph[u], f"Edge ({u} -> {v}) in path does not exist in graph"
