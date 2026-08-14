import pytest

from backend.app.algorithms.optimization.genetic_algorithm import solve_genetic_algorithm


DISTANCES = {
    "A": {"B": 2, "C": 9, "D": 12},
    "B": {"A": 2, "C": 1, "D": 2},
    "C": {"A": 9, "B": 1, "D": 1},
    "D": {"A": 12, "B": 2, "C": 1},
}


def test_genetic_algorithm_finds_a_valid_low_cost_route():
    result = solve_genetic_algorithm(
        ["A", "B", "C", "D"],
        DISTANCES,
        "A",
        "D",
        population_size=12,
        generations=25,
        seed=7,
    )

    assert result["path"][0] == "A"
    assert result["path"][-1] == "D"
    assert result["objective_cost"] == 4.0
    assert result["method"] == "genetic_algorithm"
    assert result["is_optimal"] is False


def test_genetic_algorithm_handles_start_equals_goal():
    result = solve_genetic_algorithm(["A", "B"], {"A": {"B": 1}, "B": {"A": 1}}, "A", "A")

    assert result["path"] == ["A"]
    assert result["objective_cost"] == 0.0
    assert result["visiting_order"] == ["A"]


def test_genetic_algorithm_rejects_missing_cities():
    with pytest.raises(ValueError, match="missing"):
        solve_genetic_algorithm(["A", "B"], {"A": {"B": 1}}, "A", "C")
