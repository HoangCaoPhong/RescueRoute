from types import SimpleNamespace

from backend.app.services.routing_service import run_multi_location_search


def _graph_manager():
    nodes = {
        node_id: {"id": node_id, "lat": 10.0 + node_id / 1000, "lng": 106.0}
        for node_id in (0, 1, 2, 9)
    }
    adjacency = {
        0: {1: [2.0, 1, 2.0], 2: [1.0, 1, 1.0], 9: [20.0, 1, 20.0]},
        1: {0: [2.0, 1, 2.0], 2: [1.0, 1, 1.0], 9: [1.0, 1, 1.0]},
        2: {0: [1.0, 1, 1.0], 1: [10.0, 1, 10.0], 9: [10.0, 1, 10.0]},
        9: {},
    }
    return SimpleNamespace(
        adj=adjacency,
        road_nodes=nodes,
        nodes=nodes,
        find_nearest_road_node=lambda *_args: (None, 0.0),
    )


def test_multi_location_service_returns_selected_segments_and_order():
    result = run_multi_location_search(
        _graph_manager(),
        0,
        [1, 2],
        9,
        route_algorithm="ucs",
        optimization_method="held_karp",
        criterion="cost",
    )

    assert result["found"] is True
    assert result["visiting_order"] == [0, 2, 1, 9]
    assert result["is_optimal"] is True
    assert result["order_is_optimal"] is True
    assert len(result["segments"]) == 3
    assert result["path_nodes"][0] == 0
    assert result["path_nodes"][-1] == 9


def test_multi_location_service_handles_same_start_and_goal_without_waypoints():
    result = run_multi_location_search(
        _graph_manager(),
        0,
        [],
        0,
        route_algorithm="ucs",
        optimization_method="held_karp",
    )

    assert result["found"] is True
    assert result["visiting_order"] == [0, 0]
    assert result["path_nodes"] == [0]
    assert result["objective_cost"] == 0.0
