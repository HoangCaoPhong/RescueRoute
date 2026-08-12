from typing import Any, Dict


def get_frontier_kind(algorithm: str) -> str:
    """
    Cho frontend biết cấu trúc frontier
    của từng thuật toán.
    """

    algo = (algorithm or "").lower().strip()

    if algo == "bfs":
        return "queue"

    if algo == "dfs":
        return "stack"

    if algo in {
        "ucs",
        "dijkstra",
        "astar",
        "a*",
        "greedy"
    }:
        return "priority_queue"

    if algo in {
        "hill_climbing",
        "hill-climbing"
    }:
        return "candidates"

    return "frontier"


def normalize_frontier_item(
    item: Any
) -> Dict[str, Any]:
    """
    Chuẩn hóa một phần tử frontier.

    BFS / DFS có thể trả:
        123

    UCS / Dijkstra:
        {
            "node_id": 123,
            "g": 10.5
        }

    A*:
        {
            "node_id": 123,
            "g": 10.5,
            "h": 4.2,
            "f": 14.7
        }

    Frontend luôn nhận object.
    """

    if isinstance(item, dict):

        node_id = item.get(
            "node_id",
            item.get("id")
        )

        normalized = {
            "node_id": node_id
        }

        for key in (
            "g",
            "h",
            "f",
            "cost",
            "priority"
        ):
            if key in item:
                normalized[key] = item[key]

        return normalized

    # BFS / DFS hiện tại chỉ trả node ID
    return {
        "node_id": item
    }


def build_search_trace(
    graph_mgr,
    result: Dict[str, Any],
    algorithm: str
) -> Dict[str, Any]:
    """
    Chuyển output của mọi search algorithm
    thành format visualization chung.
    """

    visited_order = (
        result.get(
            "visited_order",
            []
        )
        or []
    )

    frontier_steps = (
        result.get(
            "frontier_steps",
            []
        )
        or []
    )

    total_steps = max(
        len(visited_order),
        len(frontier_steps)
    )

    steps = []

    search_node_ids = set()

    # ======================================
    # BUILD SEARCH STEPS
    # ======================================

    for index in range(
        total_steps
    ):

        current_node = (
            visited_order[index]
            if index < len(visited_order)
            else None
        )

        raw_frontier = (
            frontier_steps[index]
            if index < len(frontier_steps)
            else []
        )

        normalized_frontier = [
            normalize_frontier_item(item)
            for item in raw_frontier
        ]

        if current_node is not None:
            search_node_ids.add(
                current_node
            )

        for item in normalized_frontier:

            node_id = item.get(
                "node_id"
            )

            if node_id is not None:
                search_node_ids.add(
                    node_id
                )

        steps.append({
            "step":
                index + 1,

            "current_node":
                current_node,

            "frontier":
                normalized_frontier
        })

    # ======================================
    # NODE ID -> COORDINATES
    # ======================================

    node_coords = {}

    for node_id in search_node_ids:

        node = (
            graph_mgr.road_nodes.get(
                node_id
            )
            or
            graph_mgr.nodes.get(
                node_id
            )
        )

        if node:

            node_coords[
                str(node_id)
            ] = [
                node["lat"],
                node["lng"]
            ]

    # ======================================
    # COMMON TRACE
    # ======================================

    return {
        "algorithm":
            algorithm,

        "frontier_kind":
            get_frontier_kind(
                algorithm
            ),

        "visited_order":
            visited_order,

        "steps":
            steps,

        "node_coords":
            node_coords
    }