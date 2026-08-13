import pytest

from backend.app.algorithms.graph_search.astar import solve_astar


WEIGHTED_GRAPH = {
    "A": {"B": {"cost": 2, "distance": 20}, "C": {"cost": 1, "distance": 10}},
    "B": {"D": {"cost": 2, "distance": 20}},
    "C": {"D": {"cost": 10, "distance": 100}},
    "D": {},
}

HEURISTIC = {"A": 3, "B": 2, "C": 4, "D": 0}


def test_astar_finds_minimum_cost_path():
    result = solve_astar(
        WEIGHTED_GRAPH,
        "A",
        "D",
        lambda node, _goal: HEURISTIC[node],
        heuristic_is_admissible=True,
    )

    assert result["path"] == ["A", "B", "D"]
    assert result["total_cost"] == 4
    assert result["total_distance"] == 40
    assert result["is_optimal"] is True


def test_astar_without_heuristic_matches_uniform_cost_search():
    result = solve_astar(WEIGHTED_GRAPH, "A", "D")

    assert result["path"] == ["A", "B", "D"]
    assert result["total_cost"] == 4
    assert result["is_optimal"] is True


def test_astar_start_equals_goal():
    result = solve_astar(WEIGHTED_GRAPH, "A", "A", lambda _node, _goal: 0)

    assert result["path"] == ["A"]
    assert result["visited_order"] == ["A"]
    assert result["explored_nodes"] == 1
    assert result["total_cost"] == 0


def test_astar_reports_search_frontier():
    result = solve_astar(
        WEIGHTED_GRAPH, "A", "D", lambda node, _goal: HEURISTIC[node]
    )

    assert result["frontier_steps"][0] == ["A"]
    assert result["frontier_steps"][1] == ["B", "C"]
    assert result["visited_order"] == ["A", "B", "D"]


def test_astar_respects_directed_edges():
    graph = {"A": {"B": 1}, "B": {}}

    assert solve_astar(graph, "A", "B")["path"] == ["A", "B"]
    with pytest.raises(ValueError, match="No route found"):
        solve_astar(graph, "B", "A")


def test_astar_avoids_high_risk_cost_edge():
    graph = {
        "A": {"B": {"cost": 100}, "C": {"cost": 2}},
        "B": {"D": {"cost": 1}},
        "C": {"D": {"cost": 2}},
        "D": {},
    }

    result = solve_astar(graph, "A", "D")

    assert result["path"] == ["A", "C", "D"]
    assert result["total_cost"] == 4


def test_astar_reopens_node_when_better_route_is_found():
    graph = {
        "S": {"A": 5, "B": 1},
        "A": {"G": 10},
        "B": {"A": 1},
        "G": {},
    }
    heuristic = {"S": 0, "A": 0, "B": 5, "G": 0}

    result = solve_astar(graph, "S", "G", lambda node, _goal: heuristic[node])

    assert result["path"] == ["S", "B", "A", "G"]
    assert result["total_cost"] == 12


@pytest.mark.parametrize("bad_cost", [-1, float("inf")])
def test_astar_rejects_invalid_edge_cost(bad_cost):
    graph = {"A": {"B": bad_cost}, "B": {}}

    with pytest.raises(ValueError, match="finite and non-negative"):
        solve_astar(graph, "A", "B")


def test_astar_rejects_invalid_node_and_heuristic():
    with pytest.raises(ValueError, match="does not exist"):
        solve_astar(WEIGHTED_GRAPH, "UNKNOWN", "D")

    with pytest.raises(ValueError, match="Heuristic"):
        solve_astar(WEIGHTED_GRAPH, "A", "D", lambda _node, _goal: -1)


def test_astar_returns_required_result_fields():
    result = solve_astar(WEIGHTED_GRAPH, "A", "D")

    assert {
        "found",
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
    }.issubset(result)
    assert result["processing_time_ms"] >= 0
