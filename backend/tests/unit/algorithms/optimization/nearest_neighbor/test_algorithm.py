from backend.app.algorithms.optimization.nearest_neighbor import (
    optimize_nearest_neighbor,
)


def test_nearest_neighbor_returns_deterministic_approximate_order():
    costs = {
        (0, 1): 1,
        (0, 2): 4,
        (1, 2): 2,
        (2, 1): 3,
        (1, 9): 5,
        (2, 9): 1,
    }

    result = optimize_nearest_neighbor(0, [2, 1], 9, costs)

    assert result["visiting_order"] == [0, 1, 2, 9]
    assert result["objective_cost"] == 4
    assert result["is_optimal"] is False
