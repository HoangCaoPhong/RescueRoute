import pytest

from backend.app.algorithms.optimization.simulated_annealing import solve_simulated_annealing


DISTANCES = {
    "A": {"B": 2, "C": 9, "D": 12},
    "B": {"A": 2, "C": 1, "D": 2},
    "C": {"A": 9, "B": 1, "D": 1},
    "D": {"A": 12, "B": 2, "C": 1},
}


def test_simulated_annealing_finds_a_valid_low_cost_route():
    result = solve_simulated_annealing(
        ["A", "B", "C", "D"],
        DISTANCES,
        "A",
        "D",
        initial_temperature=100.0,
        cooling_rate=0.9,
        min_temperature=0.1,
        iterations_per_temp=10,
        seed=7,
    )

    assert result["path"][0] == "A"
    assert result["path"][-1] == "D"
    assert result["objective_cost"] == 4.0
    assert result["method"] == "simulated_annealing"
    assert result["is_optimal"] is False


def test_simulated_annealing_handles_start_equals_goal():
    result = solve_simulated_annealing(["A", "B"], {"A": {"B": 1}, "B": {"A": 1}}, "A", "A")

    assert result["path"] == ["A"]
    assert result["objective_cost"] == 0.0
    assert result["visiting_order"] == ["A"]


def test_simulated_annealing_rejects_missing_cities():
    with pytest.raises(ValueError, match="missing"):
        solve_simulated_annealing(["A", "B"], {"A": {"B": 1}}, "A", "C")
