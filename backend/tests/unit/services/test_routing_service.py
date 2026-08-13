from backend.app.services.routing_service import run_search


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


def test_routing_service_rejects_unknown_algorithm():
    result = run_search(FakeGraphManager(), 1, 4, "unknown")

    assert result["found"] is False
    assert "Unsupported" in result["message"]
