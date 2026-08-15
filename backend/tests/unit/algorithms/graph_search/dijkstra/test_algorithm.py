from backend.app.algorithms.graph_search.dijkstra import solve_dijkstra


def test_dijkstra_uses_the_supplied_weight_and_emits_cost_trace():
    graph = {
        1: {2: [100.0, 1, 2.0], 3: [1.0, 1, 8.0]},
        2: {3: [100.0, 1, 2.0]},
        3: {},
    }

    result = solve_dijkstra(
        graph,
        1,
        3,
        edge_cost=lambda g, u, v, _profile: g[u][v][2],
    )

    assert result["path"] == [1, 2, 3]
    assert result["total_cost"] == 4.0
    event = result["trace_history"]["events"][1]
    assert event["current_node"] == 2
    assert event["frontier"][0]["g"] == 2.0
