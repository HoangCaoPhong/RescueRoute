from time import perf_counter
from backend.app.algorithms.graph_search.utils import (
    reconstruct_path,
    get_neighbors,
    has_node,
    calculate_path_metrics,
)
from backend.app.algorithms.graph_search.trace_history import SearchFailure, SearchTraceHistory


def solve_depth_limited_dfs(
    graph,
    start_node_id,
    goal_node_id,
    cost_profile=None,
    *,
    max_depth: int | None = None,
    max_expansions: int | None = 5000,
):
    """
    Depth-Limited / Bounded Search (DLS / Bounded DFS).

    Explores branches up to a maximum depth or maximum number of node expansions,
    preventing infinite loops or memory overload on large cyclic road graphs.
    """
    start_time = perf_counter()

    # Validate input nodes
    if not has_node(graph, start_node_id) or not has_node(graph, goal_node_id):
        raise ValueError(
            f"Start node '{start_node_id}' or "
            f"goal node '{goal_node_id}' does not exist."
        )

    # stack items: (node_id, parent_node_id, depth)
    stack = [(start_node_id, None, 0)]
    visited = set()
    parent = {}

    trace_history = SearchTraceHistory()

    while stack:
        current_node, current_parent, current_depth = stack.pop()

        if current_node in visited:
            continue

        frontier_preview = [node for node, _, _ in stack[:4999]] + [current_node]
        trace_history.record_expansion(
            current_node,
            frontier_preview,
        )
        visited.add(current_node)
        parent[current_node] = current_parent

        # Goal found
        if current_node == goal_node_id:
            path = reconstruct_path(parent, goal_node_id)
            total_distance, estimated_time, total_cost = calculate_path_metrics(
                graph, path, cost_profile
            )
            processing_time_ms = (perf_counter() - start_time) * 1000.0

            return {
                "found": True,
                "path": path,
                **trace_history.as_result_fields(),
                "total_distance": total_distance,
                "estimated_time": estimated_time,
                "total_cost": total_cost,
                "explored_nodes": trace_history.explored_nodes,
                "processing_time_ms": processing_time_ms,
                "is_optimal": False,
                "explanation_data": {
                    "algorithm": "DFS (Depth-Limited)",
                    "optimality": "none",
                    "message": (
                        "DFS explores graph branches to maximum depth with expansion limits. "
                        "It does not guarantee minimum distance, time, or cost."
                    )
                },
            }

        if max_expansions is not None and trace_history.explored_nodes >= max_expansions:
            message = (
                f"DFS reached maximum expansion limit ({max_expansions}) "
                f"without finding goal '{goal_node_id}'."
            )
            raise SearchFailure(
                message,
                {
                    "found": False,
                    "path": [],
                    **trace_history.as_result_fields(),
                    "explored_nodes": trace_history.explored_nodes,
                    "processing_time_ms": (perf_counter() - start_time) * 1000.0,
                    "message": message,
                },
            )

        if max_depth is not None and current_depth >= max_depth:
            continue

        # Expand neighbors: push in reverse order so LIFO pops smaller IDs first
        neighbors = get_neighbors(graph, current_node)
        for neighbor_node in reversed(neighbors):
            if neighbor_node not in visited:
                stack.append((neighbor_node, current_node, current_depth + 1))

    # No route found
    message = f"No route found from '{start_node_id}' to '{goal_node_id}'."
    raise SearchFailure(
        message,
        {
            "found": False,
            "path": [],
            **trace_history.as_result_fields(),
            "explored_nodes": trace_history.explored_nodes,
            "processing_time_ms": (perf_counter() - start_time) * 1000.0,
            "message": message,
        },
    )


def solve_dfs(
    graph,
    start_node_id,
    goal_node_id,
    cost_profile=None,
):
    """
    Standard Depth-First Search (DFS).

    Pure, unconstrained DFS exploring graph paths using a LIFO stack.
    """
    return solve_depth_limited_dfs(
        graph,
        start_node_id,
        goal_node_id,
        cost_profile=cost_profile,
        max_depth=None,
        max_expansions=None,
    )


solve_bounded_dfs = solve_depth_limited_dfs


