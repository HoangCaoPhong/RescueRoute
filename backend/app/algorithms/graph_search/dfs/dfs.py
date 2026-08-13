from time import perf_counter
from backend.app.algorithms.graph_search.utils import reconstruct_path, get_neighbors
from backend.app.algorithms.graph_search.trace_history import SearchTraceHistory


def has_node(graph, node_id):
    """Check whether node exists in graph."""
    if isinstance(graph, dict):
        return node_id in graph
    return graph.has_node(node_id)


def calculate_path_metrics(graph, path, cost_profile):
    """
    Calculate route metrics after DFS has found a path.
    DFS does not use these metrics to choose which node to explore.
    """
    if hasattr(graph, "calculate_path_metrics"):
        return graph.calculate_path_metrics(path, cost_profile)
    return None, None, None


def solve_dfs(
    graph,
    start_node_id,
    goal_node_id,
    cost_profile=None
):
    """
    Depth-First Search (DFS).

    DFS uses a LIFO stack and explores graph paths as deeply as possible
    before backtracking.

    It does not guarantee an optimal or minimum-hop path.
    """
    start_time = perf_counter()

    # Validate input nodes
    if not has_node(graph, start_node_id) or not has_node(graph, goal_node_id):
        raise ValueError(
            f"Start node '{start_node_id}' or "
            f"goal node '{goal_node_id}' does not exist."
        )

    stack = [(start_node_id, None)]
    visited = set()
    parent = {}

    trace_history = SearchTraceHistory()

    while stack:
        current_node, current_parent = stack.pop()

        if current_node in visited:
            continue

        # Re-add the popped node so the snapshot is the pre-expansion stack.
        trace_history.record_expansion(
            current_node,
            [node for node, _ in stack] + [current_node],
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
                    "algorithm": "DFS",
                    "optimality": "none",
                    "message": (
                        "DFS explores graph branches to maximum depth. "
                        "It does not guarantee minimum distance, time, or cost."
                    )
                },
            }

        # Expand neighbors: push in reverse order so LIFO pops smaller IDs first
        neighbors = get_neighbors(graph, current_node)
        for neighbor_node in reversed(neighbors):
            if neighbor_node not in visited:
                stack.append((neighbor_node, current_node))

    # No route found
    raise ValueError(f"No route found from '{start_node_id}' to '{goal_node_id}'.")
