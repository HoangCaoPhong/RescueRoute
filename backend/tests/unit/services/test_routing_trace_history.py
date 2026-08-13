from types import SimpleNamespace

import pytest

from backend.app.services.routing_service import (
    run_search,
    run_search_nearest_hospital,
)


@pytest.fixture
def graph_manager():
    road_nodes = {
        1: {"id": 1, "lat": 10.7000, "lng": 106.6000},
        2: {"id": 2, "lat": 10.7010, "lng": 106.6010},
        3: {"id": 3, "lat": 10.7020, "lng": 106.6020},
        4: {"id": 4, "lat": 10.7030, "lng": 106.6030},
    }
    adjacency = {
        1: {2: [1.0, 1, 100.0], 3: [5.0, 1, 400.0]},
        2: {4: [1.0, 1, 100.0]},
        3: {4: [1.0, 1, 100.0]},
        4: {},
    }
    hospital = {"node_id": 4, "name": "Test Hospital"}
    return SimpleNamespace(
        adj=adjacency,
        road_nodes=road_nodes,
        nodes=road_nodes,
        hospitals=[hospital],
        emergency_hospitals=[hospital],
        hospital_kdtree=None,
        emergency_hospital_kdtree=None,
        find_nearest_road_node=lambda _lat, _lng: (None, 0.0),
    )


@pytest.mark.parametrize("algorithm", ["bfs", "dfs", "ucs", "astar", "dijkstra"])
def test_every_route_algorithm_returns_a_replayable_trace(graph_manager, algorithm):
    result = run_search(graph_manager, 1, 4, algorithm)

    assert result["found"] is True
    assert result["algorithm"] == algorithm
    assert result["path_nodes"][0] == 1
    assert result["path_nodes"][-1] == 4

    trace = result["search_trace"]
    assert trace["algorithm"] == algorithm
    assert len(trace["steps"]) == result["nodes_expanded"]
    assert trace["visited_order"][-1] == 4
    assert trace["steps"][-1]["current_node"] == 4

    for step in trace["steps"]:
        assert str(step["current_node"]) in trace["node_coords"]
        assert all("node_id" in item for item in step["frontier"])


@pytest.mark.parametrize("algorithm", ["bfs", "dfs", "ucs", "astar", "dijkstra"])
def test_nearest_hospital_search_uses_the_same_trace_contract(graph_manager, algorithm):
    result = run_search_nearest_hospital(graph_manager, 1, algorithm)

    assert result["found"] is True
    assert result["destination_hospital"]["node_id"] == 4
    assert len(result["search_trace"]["steps"]) == result["nodes_expanded"]
    assert result["search_trace"]["steps"][-1]["current_node"] == 4
