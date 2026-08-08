from backend.app.algorithms.graph_search.bfs.bfs import bfs

from backend.tests.fixtures.bfs_graphs import (
    MINIMUM_HOP_GRAPH,
    DIRECTED_GRAPH,
    NO_PATH_GRAPH,
    DUPLICATE_DISCOVERY_GRAPH,
)

def test_bfs_finds_minimum_hop_path():
    result = bfs(
        MINIMUM_HOP_GRAPH,
        "A",
        "D"
    )
    assert result["path"] == ["A", "B", "D"]
    assert result["hop_count"] == 2

def test_bfs_no_path():
    result = bfs(
        NO_PATH_GRAPH,
        "A",
        "C"
    )
    assert result["path"] is None
    assert result["hop_count"] is None

def test_bfs_respects_direction():
    forward = bfs(
        DIRECTED_GRAPH,
        "A",
        "B"
    )
    assert forward["path"] == ["A", "B"]

    backward = bfs(
        DIRECTED_GRAPH,
        "B",
        "A"
    )
    assert backward["path"] is None

def test_bfs_does_not_visit_node_twice():
    result = bfs(
        DUPLICATE_DISCOVERY_GRAPH,
        "A",
        "D"
    )

    explored = result["explored_order"]
    assert len(explored) == len(set(explored))

def test_bfs_frontier_steps():

    result = bfs(
        MINIMUM_HOP_GRAPH,
        "A",
        "D"
    )
    steps = result["frontier_steps"]

    assert steps[0]["current"] == "A"
    assert steps[0]["frontier"] == ["B", "C"]
    assert steps[0]["explored"] == ["A"]
    assert steps[1]["current"] == "B"
    assert steps[1]["frontier"] == ["C", "D"]

def test_bfs_start_equals_goal():

    result = bfs(
        DIRECTED_GRAPH,
        "A",
        "A"
    )
    assert result["path"] == ["A"]
    assert result["hop_count"] == 0
    assert result["explored_order"] == ["A"]