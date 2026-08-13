from backend.app.algorithms.graph_search.trace_history import SearchTraceHistory


def test_trace_history_keeps_an_immutable_frontier_snapshot():
    history = SearchTraceHistory()
    frontier = [{"node_id": 1, "g": 0.0}, {"node_id": 2, "g": 4.5}]

    history.record_expansion(1, frontier)
    frontier[1]["g"] = 999.0
    history.record_expansion(2, [2, 3])

    fields = history.as_result_fields()

    assert fields["visited_order"] == [1, 2]
    assert fields["frontier_steps"][0] == [
        {"node_id": 1, "g": 0.0},
        {"node_id": 2, "g": 4.5},
    ]
    assert fields["trace_history"] == {
        "version": "1.0",
        "events": [
            {
                "step": 1,
                "current_node": 1,
                "frontier": [
                    {"node_id": 1, "g": 0.0},
                    {"node_id": 2, "g": 4.5},
                ],
            },
            {
                "step": 2,
                "current_node": 2,
                "frontier": [2, 3],
            },
        ],
    }


def test_trace_history_exposes_legacy_fields_for_algorithm_compatibility():
    history = SearchTraceHistory()
    history.record_expansion("A", ["A"])

    fields = history.as_result_fields()

    assert history.explored_nodes == 1
    assert fields["visited_order"] == ["A"]
    assert fields["frontier_steps"] == [["A"]]
