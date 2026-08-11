def reconstruct_path(parent, goal_node_id):
    """Reconstruct path from start node to goal node."""
    path = []
    current = goal_node_id

    while current is not None:
        path.append(current)
        current = parent[current]

    return path[::-1]


def get_neighbors(graph, node_id):
    """Get neighbors in deterministic order."""

    if isinstance(graph, dict):
        # Our defaultdict structure: graph[node_id] is a dict where keys are neighbors
        neighbors = graph.get(node_id, {}).keys()
        return sorted(list(neighbors))

    # Common Graph abstraction
    edges = graph.get_neighbors(node_id)
    return sorted([edge.v for edge in edges])
