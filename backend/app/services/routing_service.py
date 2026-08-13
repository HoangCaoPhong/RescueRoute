import math
import time
import heapq
from collections import deque
from typing import Dict, Any, Optional

from backend.app.algorithms.graph_search.bfs.bfs import solve_bfs
from backend.app.algorithms.graph_search.astar import solve_astar
from backend.app.algorithms.optimization.hill_climbing import solve_hill_climbing

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000.0
    r_lat1, r_lng1 = math.radians(lat1), math.radians(lng1)
    r_lat2, r_lng2 = math.radians(lat2), math.radians(lng2)
    dlat = r_lat2 - r_lat1
    dlng = r_lng2 - r_lng1
    a = math.sin(dlat/2)**2 + math.cos(r_lat1)*math.cos(r_lat2)*math.sin(dlng/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def run_search(graph_mgr, start_id: int, goal_id: int, algorithm: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    
    # Kiểm tra và ánh xạ nếu node nằm ngoài road_nodes
    if start_id not in graph_mgr.adj:
        node = graph_mgr.nodes.get(start_id)
        if node:
            nearest, _ = graph_mgr.find_nearest_road_node(node["lat"], node["lng"])
            if nearest:
                start_id = nearest["id"]

    if goal_id not in graph_mgr.adj:
        node = graph_mgr.nodes.get(goal_id)
        if node:
            nearest, _ = graph_mgr.find_nearest_road_node(node["lat"], node["lng"])
            if nearest:
                goal_id = nearest["id"]

    if start_id not in graph_mgr.road_nodes or goal_id not in graph_mgr.road_nodes:
        return {"found": False, "execution_time_ms": (time.perf_counter() - t0) * 1000}

    algo = algorithm.lower().strip()
    goal_node = graph_mgr.road_nodes[goal_id]
    start_node = graph_mgr.road_nodes[start_id]
    parent: Dict[int, Optional[int]] = {start_id: None}
    nodes_expanded = 0
    found = False

    if start_id == goal_id:
        return {
            "found": True,
            "total_cost": 0.0,
            "total_distance_m": 0.0,
            "nodes_expanded": 1,
            "execution_time_ms": (time.perf_counter() - t0) * 1000,
            "path_coords": [[goal_node["lat"], goal_node["lng"]]],
            "path_nodes": [start_id]
        }

    # Helper function for coordinate mapping
    def build_path_response(path_nodes, exec_time, expanded=0):
        total_cost = 0.0
        total_dist = 0.0
        path_coords = []
        for i in range(len(path_nodes)):
            node = graph_mgr.road_nodes.get(path_nodes[i]) or graph_mgr.nodes.get(path_nodes[i])
            if node:
                path_coords.append([node["lat"], node["lng"]])
            if i < len(path_nodes) - 1:
                edge = graph_mgr.adj.get(path_nodes[i], {}).get(path_nodes[i+1])
                if edge:
                    total_cost += edge[0]
                    total_dist += edge[2]

        return {
            "found": True,
            "total_cost": round(total_cost, 2),
            "total_distance_m": round(total_dist, 2),
            "nodes_expanded": expanded,
            "execution_time_ms": round(exec_time, 2),
            "path_coords": path_coords,
            "path_nodes": path_nodes
        }

    if algo == "bfs":
        result = solve_bfs(graph_mgr.adj, start_id, goal_id)
        exec_time = (time.perf_counter() - t0) * 1000
        
        if not result.get("found", True) or not result.get("path"):
            return {
                "found": False,
                "nodes_expanded": result.get("explored_nodes", 0),
                "execution_time_ms": round(exec_time, 2)
            }
            
        # BFS was successful
        path = result["path"]
        expanded = result.get("explored_nodes", len(result.get("visited_order", [])))
        return build_path_response(path, exec_time, expanded)

    elif algo == "dfs":
        stack = [start_id]
        visited = {start_id}
        while stack:
            curr = stack.pop()
            nodes_expanded += 1
            if curr == goal_id:
                found = True
                break
            for nbr in graph_mgr.adj.get(curr, {}):
                if nbr not in visited:
                    visited.add(nbr)
                    parent[nbr] = curr
                    stack.append(nbr)

    elif algo == "dijkstra":
        pq = [(0.0, start_id)]
        best_dist = {start_id: 0.0}
        while pq:
            d, curr = heapq.heappop(pq)
            if d > best_dist.get(curr, float('inf')):
                continue
            nodes_expanded += 1
            if curr == goal_id:
                found = True
                break
            for nbr, edge in graph_mgr.adj.get(curr, {}).items():
                new_d = d + edge[2]
                if new_d < best_dist.get(nbr, float('inf')):
                    best_dist[nbr] = new_d
                    parent[nbr] = curr
                    heapq.heappush(pq, (new_d, nbr))

    elif algo in {"astar", "ucs", "hill_climbing", "hill-climbing"}:
        def h(n_id: int) -> float:
            node = graph_mgr.road_nodes.get(n_id)
            if not node:
                return 0.0
            distance = haversine(
                node["lat"], node["lng"], goal_node["lat"], goal_node["lng"]
            )
            return distance if algo.startswith("hill") else distance * 0.035

        try:
            if algo.startswith("hill"):
                result = solve_hill_climbing(
                    graph_mgr.adj,
                    start_id,
                    goal_id,
                    lambda node_id, _goal_id: h(node_id),
                )
            else:
                result = solve_astar(
                    graph_mgr.adj,
                    start_id,
                    goal_id,
                    None if algo == "ucs" else lambda node_id, _goal_id: h(node_id),
                )
        except ValueError as error:
            return {
                "found": False,
                "nodes_expanded": 0,
                "execution_time_ms": round((time.perf_counter() - t0) * 1000, 2),
                "message": str(error),
            }

        exec_time = (time.perf_counter() - t0) * 1000
        return build_path_response(
            result["path"], exec_time, result["explored_nodes"]
        )

    else:
        return {
            "found": False,
            "nodes_expanded": 0,
            "execution_time_ms": round((time.perf_counter() - t0) * 1000, 2),
            "message": f"Unsupported search algorithm: '{algorithm}'.",
        }

    exec_time = (time.perf_counter() - t0) * 1000

    if not found:
        return {
            "found": False,
            "nodes_expanded": nodes_expanded,
            "execution_time_ms": round(exec_time, 2)
        }

    # Tái hiện đường đi (cho DFS, Dijkstra, A*, UCS)
    path = []
    curr = goal_id
    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)
    path.reverse()

    return build_path_response(path, exec_time, nodes_expanded)
