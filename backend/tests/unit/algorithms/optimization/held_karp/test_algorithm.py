import pytest

from backend.app.algorithms.optimization.held_karp import optimize_held_karp


def test_held_karp_finds_the_optimal_fixed_endpoint_order():
    costs = {
        (0, 1): 2,
        (0, 2): 1,
        (1, 2): 1,
        (2, 1): 20,
        (1, 9): 1,
        (2, 9): 10,
    }

    result = optimize_held_karp(0, [1, 2], 9, costs)

    assert result["visiting_order"] == [0, 1, 2, 9]
    assert result["objective_cost"] == 13
    assert result["is_optimal"] is True


def test_held_karp_reports_an_unreachable_complete_tour():
    with pytest.raises(ValueError, match="visit every waypoint"):
        optimize_held_karp(0, [1, 2], 9, {(0, 1): 1})
