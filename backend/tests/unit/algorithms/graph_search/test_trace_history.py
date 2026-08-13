from backend.app.algorithms.graph_search.trace_history import (
    MAX_FRONTIER_ITEMS,
    SearchTraceHistory,
)


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
                "frontier_size": 2,
                "frontier_truncated": False,
            },
            {
                "step": 2,
                "current_node": 2,
                "frontier": [2, 3],
                "frontier_size": 2,
                "frontier_truncated": False,
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


def test_trace_history_caps_wide_frontiers_and_reports_full_size():
    history = SearchTraceHistory()
    frontier = list(range(MAX_FRONTIER_ITEMS + 20))

    history.record_expansion(0, frontier)
    event = history.as_result_fields()["trace_history"]["events"][0]

    assert len(event["frontier"]) == MAX_FRONTIER_ITEMS
    assert event["frontier_size"] == len(frontier)
    assert event["frontier_truncated"] is True
