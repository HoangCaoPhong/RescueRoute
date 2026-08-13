from types import SimpleNamespace

import pytest

from backend.app.services.routing_service import run_search


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
    return SimpleNamespace(
        adj=adjacency,
        road_nodes=road_nodes,
        nodes=road_nodes,
        find_nearest_road_node=lambda _lat, _lng: (None, 0.0),
    )


@pytest.mark.parametrize("algorithm", ["bfs", "dfs", "ucs", "astar", "dijkstra"])
def test_route_result_contains_complete_visualization_payload(
    graph_manager, algorithm
):
    result = run_search(graph_manager, 1, 4, algorithm)

    assert result["found"] is True
    assert result["algorithm"] == algorithm
    assert result["path_nodes"][0] == 1
    assert result["path_nodes"][-1] == 4

    trace = result["search_trace"]
    assert trace["algorithm"] == algorithm
    assert trace["visited_order"]
    assert len(trace["steps"]) == len(trace["visited_order"])
    assert trace["steps"][-1]["current_node"] == 4

    traced_node_ids = {
        step["current_node"]
        for step in trace["steps"]
        if step["current_node"] is not None
    }
    assert traced_node_ids.issubset({int(node_id) for node_id in trace["node_coords"]})


def test_start_equals_goal_still_returns_a_trace(graph_manager):
    result = run_search(graph_manager, 1, 1, "astar")

    assert result["path_nodes"] == [1]
    assert result["search_trace"]["visited_order"] == [1]
    assert result["search_trace"]["steps"] == [
        {
            "step": 1,
            "current_node": 1,
            "frontier": [{"node_id": 1}],
            "frontier_size": 1,
            "frontier_truncated": False,
        }
    ]


class FakeGraphManager:
    def __init__(self):
        self.adj = {
            1: {2: [1.0, 1, 100.0], 3: [5.0, 1, 300.0]},
            2: {4: [1.0, 1, 100.0]},
            3: {4: [1.0, 1, 100.0]},
            4: {},
        }
        self.road_nodes = {
            1: {"id": 1, "lat": 0.0, "lng": 0.0},
            2: {"id": 2, "lat": 0.0, "lng": 0.002},
            3: {"id": 3, "lat": 0.01, "lng": 0.01},
            4: {"id": 4, "lat": 0.0, "lng": 0.003},
        }
        self.nodes = self.road_nodes

    def find_nearest_road_node(self, _lat, _lng):
        return None, 0.0


def test_routing_service_dispatches_to_astar_module():
    result = run_search(FakeGraphManager(), 1, 4, "astar")

    assert result["found"] is True
    assert result["path_nodes"] == [1, 2, 4]
    assert result["total_cost"] == 2.0


def test_routing_service_dispatches_to_hill_climbing_module():
    result = run_search(FakeGraphManager(), 1, 4, "hill_climbing")

    assert result["found"] is True
    assert result["path_nodes"] == [1, 2, 4]
    first_candidate = result["search_trace"]["steps"][0]["frontier"][0]
    assert "h" in first_candidate
    assert first_candidate["selected"] is True


def test_routing_service_rejects_unknown_algorithm():
    result = run_search(FakeGraphManager(), 1, 4, "unknown")

    assert result["found"] is False
    assert "Unsupported" in result["message"]
