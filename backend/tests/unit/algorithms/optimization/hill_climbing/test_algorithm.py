import pytest

from backend.app.algorithms.optimization.hill_climbing import solve_hill_climbing


GRAPH = {
    "A": {"B": {"cost": 2, "distance": 20}, "C": {"cost": 5, "distance": 50}},
    "B": {"D": {"cost": 3, "distance": 30}},
    "C": {},
    "D": {},
}
HEURISTIC = {"A": 4, "B": 2, "C": 3, "D": 0}


def test_hill_climbing_follows_best_neighbor_to_goal():
    result = solve_hill_climbing(
        GRAPH, "A", "D", lambda node, _goal: HEURISTIC[node]
    )

    assert result["path"] == ["A", "B", "D"]
    assert result["visited_order"] == ["A", "B", "D"]
    assert result["total_cost"] == 5
    assert result["total_distance"] == 50
    assert result["is_optimal"] is False


def test_hill_climbing_start_equals_goal():
    result = solve_hill_climbing(GRAPH, "A", "A", lambda _node, _goal: 0)

    assert result["path"] == ["A"]
    assert result["explored_nodes"] == 1
    assert result["frontier_steps"] == [[]]


def test_hill_climbing_reports_ranked_candidates():
    result = solve_hill_climbing(
        GRAPH, "A", "D", lambda node, _goal: HEURISTIC[node]
    )

    assert [item["node_id"] for item in result["frontier_steps"][0]] == ["B", "C"]
    assert result["heuristic_steps"][0] == {
        "current": "A",
        "current_heuristic": 4,
        "selected": "B",
        "selected_heuristic": 2,
    }


def test_hill_climbing_stops_at_local_optimum():
    graph = {"A": {"B": 1}, "B": {"G": 1}, "G": {}}
    heuristic = {"A": 2, "B": 3, "G": 0}

    with pytest.raises(ValueError, match="local optimum"):
        solve_hill_climbing(graph, "A", "G", lambda node, _goal: heuristic[node])


def test_hill_climbing_can_cross_plateau_when_enabled():
    graph = {"A": {"B": 1}, "B": {"G": 1}, "G": {}}
    heuristic = {"A": 2, "B": 2, "G": 0}

    result = solve_hill_climbing(
        graph,
        "A",
        "G",
        lambda node, _goal: heuristic[node],
        allow_sideways=True,
    )

    assert result["path"] == ["A", "B", "G"]


def test_hill_climbing_respects_directed_graph():
    graph = {"A": {"B": 1}, "B": {}}
    heuristic = {"A": 1, "B": 0}

    assert solve_hill_climbing(
        graph, "A", "B", lambda node, _goal: heuristic[node]
    )["path"] == ["A", "B"]
    with pytest.raises(ValueError, match="dead end"):
        solve_hill_climbing(
            graph, "B", "A", lambda node, _goal: 0 if node == "A" else 1
        )


def test_hill_climbing_uses_deterministic_tie_break():
    graph = {"A": {"C": 1, "B": 1}, "B": {"G": 1}, "C": {}, "G": {}}
    heuristic = {"A": 2, "B": 1, "C": 1, "G": 0}

    result = solve_hill_climbing(
        graph, "A", "G", lambda node, _goal: heuristic[node]
    )

    assert result["path"] == ["A", "B", "G"]


def test_hill_climbing_honors_max_steps():
    with pytest.raises(ValueError, match="within 1 steps"):
        solve_hill_climbing(
            GRAPH,
            "A",
            "D",
            lambda node, _goal: HEURISTIC[node],
            max_steps=1,
        )


def test_hill_climbing_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="does not exist"):
        solve_hill_climbing(GRAPH, "UNKNOWN", "D", lambda _node, _goal: 0)
    with pytest.raises(ValueError, match="max_steps"):
        solve_hill_climbing(GRAPH, "A", "D", lambda _node, _goal: 0, max_steps=-1)
    with pytest.raises(ValueError, match="Heuristic"):
        solve_hill_climbing(GRAPH, "A", "D", lambda _node, _goal: float("nan"))


def test_hill_climbing_returns_required_result_fields():
    result = solve_hill_climbing(
        GRAPH, "A", "D", lambda node, _goal: HEURISTIC[node]
    )

    assert {
        "found",
        "path",
        "visited_order",
        "frontier_steps",
        "heuristic_steps",
        "total_distance",
        "estimated_time",
        "total_cost",
        "explored_nodes",
        "processing_time_ms",
        "is_optimal",
        "explanation_data",
    }.issubset(result)
    assert result["processing_time_ms"] >= 0
