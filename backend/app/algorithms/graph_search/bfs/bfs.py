import csv
from collections import deque
from pathlib import Path
from time import perf_counter


def load_graph(edges_file):
    """
    Convert edges.csv to directed adjacency list.

    graph[u] = [v1, v2, ...]
    """

    graph = {}

    with open(edges_file, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            u = row["source_node_id"]
            v = row["target_node_id"]

            graph.setdefault(u, []).append(v)
            graph.setdefault(v, [])

    return graph


def reconstruct_path(parent, goal):
    """Reconstruct path from start to goal."""

    path = []
    current = goal

    while current is not None:
        path.append(current)
        current = parent[current]

    return path[::-1]   #đảo ngược để truy tìm đường đi


def bfs(graph, start, goal):
    """
    Breadth-First Search.

    BFS finds a path with the minimum number of edges (hops).
    It does not optimize distance, time, congestion, or cost.
    """

    start = str(start)
    goal = str(goal)

    if start not in graph or goal not in graph:
        return None

    queue = deque([start])
    visited = {start}

    parent = {
        start: None
    }

    explored_order = []
    frontier_steps = []

    start_time = perf_counter()

    while queue:
        current = queue.popleft()

        explored_order.append(current)

        if current == goal:
            frontier_steps.append({
                "current": current,
                "frontier": list(queue),
                "explored": explored_order.copy()
            })
            path = reconstruct_path(parent, goal)

            processing_time_ms = (
                perf_counter() - start_time
            ) * 1000

            return {
                "path": path,
                "hop_count": len(path) - 1,
                "explored_order": explored_order,
                "explored_count": len(explored_order),
                "processing_time_ms": processing_time_ms
            }

        for neighbor in graph[current]:

            if neighbor not in visited:
                visited.add(neighbor)

                parent[neighbor] = current

                queue.append(neighbor)

        # Save BFS state after expanding current node
        frontier_steps.append({
            "current": current,
            "frontier": list(queue),
            "explored": explored_order.copy()
        })
    processing_time_ms = (perf_counter() - start_time) * 1000
    return {
        "path": None,
        "hop_count": None,
        "explored_order": explored_order,
        "explored_count": len(explored_order),
        "frontier_steps": frontier_steps,
        "processing_time_ms": processing_time_ms
    }

#demo test
if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[5]

    edges_file = (
        project_root
        / "data"
        / "samples"
        / "simulated_vietnamese_traffic"
        / "edges.csv"
    )

    graph = load_graph(edges_file)

    print("Number of nodes:", len(graph))

    number_of_edges = sum(
        len(neighbors)
        for neighbors in graph.values()
    )

    print("Number of edges:", number_of_edges)

    start = "4658499310"
    goal = "366453620"

    result = bfs(graph, start, goal)

    print("Path:", result["path"])
    print("Hop count:", result["hop_count"])
    print("Explored:", result["explored_order"])
    print("Explored count:", result["explored_count"])
    print("Processing time:", result["processing_time_ms"], "ms")  

     