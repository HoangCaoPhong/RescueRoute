import heapq
from time import perf_counter

from backend.app.algorithms.graph_search.utils import reconstruct_path, get_neighbors


def has_node(graph, node_id):
    """Check whether node exists in graph."""
    if isinstance(graph, dict):
        return node_id in graph

    return graph.has_node(node_id)


def calculate_path_metrics(graph, path, cost_profile):
    """
    Calculate route metrics after UCS has found a path.
    """
    if hasattr(graph, "calculate_path_metrics"):
        return graph.calculate_path_metrics(path, cost_profile)

    return None, None, None


def get_edge_cost(graph, u, v, cost_profile=None):
    """Extract edge cost dynamically based on graph type."""
    if hasattr(graph, "get_edge_weight"):
        return graph.get_edge_weight(u, v, cost_profile)
    
    if isinstance(graph, dict):
        if u in graph:
            neighbors = graph[u]
            if isinstance(neighbors, dict) and v in neighbors:
                edge_data = neighbors[v]
                if isinstance(edge_data, (int, float)):
                    return float(edge_data)
                if isinstance(edge_data, list) and len(edge_data) > 0:
                    return float(edge_data[0])
                if isinstance(edge_data, dict):
                    return float(edge_data.get("weight", 1.0))
    
    return 1.0


def solve_ucs(graph, start_node_id, goal_node_id, cost_profile=None):
    """
    Uniform Cost Search (UCS).

    UCS uses a priority queue (min-heap) and explores the graph based on the lowest cumulative cost.
    It guarantees a minimum-cost path when all edge costs are non-negative.
    """

    try:
        start_node_id = int(start_node_id)
        goal_node_id = int(goal_node_id)
    except (ValueError, TypeError):
        pass # Allow string IDs for test fixtures

    start_time = perf_counter()

    # Validate input
    if (not has_node(graph, start_node_id) or not has_node(graph, goal_node_id)):
        raise ValueError(
            f"Start node '{start_node_id}' or "
            f"goal node '{goal_node_id}' does not exist."
        )

    # UCS initialization
    pq = [(0.0, start_node_id)]
    g_score = {start_node_id: 0.0}
    visited = set()
    parent = {start_node_id: None}
    
    visited_order = []
    frontier_steps = []

    # UCS search
    while pq:

        # Record frontier before expanding current node
        frontier_nodes = [node for _, node in pq]
        frontier_steps.append(frontier_nodes)
        
        current_cost, current_node = heapq.heappop(pq)
        
        if current_node in visited:
            continue
            
        visited.add(current_node)
        visited_order.append(current_node)

        # Goal found
        if current_node == goal_node_id:

            path = reconstruct_path(parent, goal_node_id)
            (total_distance, estimated_time, total_cost) = calculate_path_metrics(graph, path, cost_profile)

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

                "is_optimal": True,

                "explanation_data": {
                    "algorithm": "UCS",
                    "optimality": "minimum_cost",
                    "message": (
                        "UCS finds the path with the minimum cumulative cost. "
                        "It guarantees the optimal route when all edge costs are non-negative."
                    )
                },

                "total_path_cost": current_cost
            }

        # Expand neighbors
        for neighbor_node in get_neighbors(graph, current_node):
            if neighbor_node in visited:
                continue
                
            edge_cost = get_edge_cost(graph, current_node, neighbor_node, cost_profile)
            tentative_g = current_cost + edge_cost
            
            if neighbor_node not in g_score or tentative_g < g_score[neighbor_node]:
                g_score[neighbor_node] = tentative_g
                parent[neighbor_node] = current_node
                heapq.heappush(pq, (tentative_g, neighbor_node))

    # No route found
    return {
        "found": False,
        "path": [],
        "message": f"No route found from '{start_node_id}' to '{goal_node_id}'."
    }