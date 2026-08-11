from collections import deque
from time import perf_counter


from backend.app.algorithms.graph_search.utils import reconstruct_path, get_neighbors


def has_node(graph, node_id):
    """Check whether node exists in graph."""
    if isinstance(graph, dict):
        return node_id in graph

    return graph.has_node(node_id)


def calculate_path_metrics(graph, path, cost_profile):
    """
    Calculate route metrics after BFS has found a path.
    BFS does not use these metrics to choose which node to explore.
    """

    if hasattr(graph, "calculate_path_metrics"):
        return graph.calculate_path_metrics(path, cost_profile)

    # Adjacency-dict graph used in current unit tests
    # does not contain edge attributes.
    return None, None, None


def solve_bfs(
    graph,
    start_node_id,
    goal_node_id,
    cost_profile=None
):
    """
    Breadth-First Search (BFS).

    BFS uses a FIFO queue and explores the graph level by level.

    It guarantees a minimum-hop path when all edges are treated equally.
    It does not optimize distance, travel time, congestion, or traffic cost.
    """

    start_node_id = int(start_node_id)
    goal_node_id = int(goal_node_id)
    start_time = perf_counter()

    # Validate input
    if (
        not has_node(graph, start_node_id)
        or not has_node(graph, goal_node_id)
    ):
        raise ValueError(
            f"Start node '{start_node_id}' or "
            f"goal node '{goal_node_id}' does not exist."
        )

    # BFS initialization
    queue = deque([start_node_id])
    visited = {start_node_id}
    parent = {start_node_id: None}
    
    visited_order = []
    frontier_steps = []

    # BFS search
    while queue:

        # Record frontier before expanding current node
        frontier_steps.append(list(queue))
        current_node = queue.popleft()
        visited_order.append(current_node)

        # Goal found
        if current_node == goal_node_id:

            path = reconstruct_path(parent,goal_node_id)
            (total_distance,estimated_time,total_cost) = calculate_path_metrics(graph,path,cost_profile)

            processing_time_ms = (perf_counter() - start_time) * 1000.0

            return {
                "path": path,
                "visited_order": visited_order,
                "frontier_steps": frontier_steps,

                "total_distance": total_distance,
                "estimated_time": estimated_time,
                "total_cost": total_cost,

                "explored_nodes": len(visited_order),
                "processing_time_ms": processing_time_ms,

                # BFS is optimal for minimum number of hops.
                "is_optimal": True,

                "explanation_data": {
                    "algorithm": "BFS",
                    "optimality": "minimum_hops",
                    "message": (
                        "BFS finds a path with the minimum number "
                        "of edges when all edges are treated equally. "
                        "It does not guarantee minimum distance, "
                        "travel time, or traffic cost."
                    )
                },

                # BFS-specific additional metric
                "hop_count": len(path) - 1
            }

        # Expand neighbors
        for neighbor_node in get_neighbors(
            graph,
            current_node
        ):
            if neighbor_node not in visited:

                # Mark visited when inserted into queue
                # to prevent duplicate entries.
                visited.add(neighbor_node)
                parent[neighbor_node] = current_node
                queue.append(neighbor_node)

    # No route found
    return {
        "found": False,
        "path": [],
        "message": f"No route found from '{start_node_id}' to '{goal_node_id}'."
    }