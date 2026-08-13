import math
import time
import heapq
from typing import Any, Dict, Iterable, List, Optional, Tuple

from backend.app.algorithms.graph_search.bfs.bfs import solve_bfs
from backend.app.algorithms.graph_search.dfs.dfs import solve_dfs
from backend.app.services.search_trace import build_search_trace

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000.0
    r_lat1, r_lng1 = math.radians(lat1), math.radians(lng1)
    r_lat2, r_lng2 = math.radians(lat2), math.radians(lng2)
    dlat = r_lat2 - r_lat1
    dlng = r_lng2 - r_lng1
    a = math.sin(dlat/2)**2 + math.cos(r_lat1)*math.cos(r_lat2)*math.sin(dlng/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_frontier_snapshot(
    entries: Iterable[Tuple[float, float, int]],
    best_scores: Dict[int, float],
    heuristic,
) -> List[Dict[str, float | int]]:
    """Return the current, non-stale priority queue entries for the UI trace."""

    snapshot: List[Dict[str, float | int]] = []
    seen_nodes = set()
    for priority, cost, node_id in sorted(entries):
        if cost != best_scores.get(node_id) or node_id in seen_nodes:
            continue
        seen_nodes.add(node_id)
        heuristic_cost = heuristic(node_id)
        snapshot.append(
            {
                "node_id": node_id,
                "g": round(cost, 2),
                "h": round(heuristic_cost, 2),
                "f": round(priority, 2),
            }
        )
    return snapshot


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

    def build_success_response(
        path_nodes: List[int],
        exec_time: float,
        expanded: int,
        trace_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Keep the route and visualization payload in one response contract."""

        response = build_path_response(path_nodes, exec_time, expanded)
        response["algorithm"] = algo
        response["search_trace"] = build_search_trace(
            graph_mgr,
            trace_result,
            algo,
        )
        return response

    if start_id == goal_id:
        execution_time = (time.perf_counter() - t0) * 1000
        return build_success_response(
            [start_id],
            execution_time,
            1,
            {
                "visited_order": [start_id],
                "frontier_steps": [[start_id]],
            },
        )

    if algo == "bfs":
        result = solve_bfs(graph_mgr.adj, start_id, goal_id)
        exec_time = (time.perf_counter() - t0) * 1000
        
        if not result.get("found", True) or not result.get("path"):
            return {
                "found": False,
                "algorithm": "bfs",
                "nodes_expanded": result.get("explored_nodes", 0),
                "execution_time_ms": round(exec_time, 2),
                "message": result.get(
                    "message",
                    f"No route found from '{start_id}' to '{goal_id}'."
                )
            }
            
        # BFS was successful
        path = result["path"]
        expanded = result.get("explored_nodes", len(result.get("visited_order", [])))
        response = build_success_response(path, exec_time, expanded, result)
        response["explanation_data"] = result.get("explanation_data", {})
        response["hop_count"] = result.get("hop_count")
        response["is_optimal"] = result.get("is_optimal")
        return response

    elif algo == "dfs":
        try:
            result = solve_dfs(graph_mgr.adj, start_id, goal_id)
            exec_time = (time.perf_counter() - t0) * 1000

            if not result.get("found", True) or not result.get("path"):
                return {
                    "found": False,
                    "nodes_expanded": result.get("explored_nodes", 0),
                    "execution_time_ms": round(exec_time, 2)
                }

            path = result["path"]
            expanded = result.get("explored_nodes", len(result.get("visited_order", [])))
            response = build_success_response(path, exec_time, expanded, result)
            response["explanation_data"] = result.get("explanation_data", {})
            response["is_optimal"] = result.get("is_optimal")
            return response
        except ValueError:
            exec_time = (time.perf_counter() - t0) * 1000
            return {
                "found": False,
                "nodes_expanded": 0,
                "execution_time_ms": round(exec_time, 2)
            }

    elif algo == "dijkstra":
        pq = [(0.0, start_id)]
        best_dist = {start_id: 0.0}
        visited_order = []
        frontier_steps = []
        while pq:
            d, curr = heapq.heappop(pq)
            if d > best_dist.get(curr, float('inf')):
                continue
            nodes_expanded += 1
            visited_order.append(curr)
            frontier_steps.append(
                [
                    {"node_id": curr, "g": round(d, 2), "f": round(d, 2)},
                    *[
                        {"node_id": node_id, "g": round(cost, 2), "f": round(cost, 2)}
                        for cost, node_id in sorted(pq)
                        if cost == best_dist.get(node_id)
                    ],
                ]
            )
            if curr == goal_id:
                found = True
                break
            for nbr, edge in graph_mgr.adj.get(curr, {}).items():
                new_d = d + edge[2]
                if new_d < best_dist.get(nbr, float('inf')):
                    best_dist[nbr] = new_d
                    parent[nbr] = curr
                    heapq.heappush(pq, (new_d, nbr))

    else:  # Mặc định A* và UCS
        def h(n_id: int) -> float:
            if algo == "ucs":
                return 0.0
            node = graph_mgr.road_nodes.get(n_id)
            if not node:
                return 0.0
            return haversine(node["lat"], node["lng"], goal_node["lat"], goal_node["lng"]) * 0.035

        pq = [(h(start_id), 0.0, start_id)]
        g_scores = {start_id: 0.0}
        visited_order = []
        frontier_steps = []

        while pq:
            f, g, curr = heapq.heappop(pq)
            if g > g_scores.get(curr, float('inf')):
                continue
            nodes_expanded += 1
            visited_order.append(curr)
            frontier_steps.append(
                [
                    {
                        "node_id": curr,
                        "g": round(g, 2),
                        "h": round(h(curr), 2),
                        "f": round(f, 2),
                    },
                    *_build_frontier_snapshot(pq, g_scores, h),
                ]
            )
            if curr == goal_id:
                found = True
                break
            for nbr, edge in graph_mgr.adj.get(curr, {}).items():
                tentative_g = g + edge[0]
                if tentative_g < g_scores.get(nbr, float('inf')):
                    g_scores[nbr] = tentative_g
                    parent[nbr] = curr
                    heapq.heappush(pq, (tentative_g + h(nbr), tentative_g, nbr))

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

    return build_success_response(
        path,
        exec_time,
        nodes_expanded,
        {
            "visited_order": visited_order,
            "frontier_steps": frontier_steps,
        },
    )
