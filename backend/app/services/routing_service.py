import math
import time
import heapq
from collections import deque
from typing import Dict, Any, Optional
import numpy as np

from backend.app.algorithms.graph_search.bfs.bfs import solve_bfs
from backend.app.algorithms.graph_search.dfs.dfs import solve_dfs

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
        try:
            result = solve_bfs(graph_mgr.adj, start_id, goal_id)
            exec_time = (time.perf_counter() - t0) * 1000
            
            if not result.get("found", True) or not result.get("path"):
                return {
                    "found": False,
                    "nodes_expanded": result.get("explored_nodes", 0),
                    "execution_time_ms": round(exec_time, 2)
                }
                
            path = result["path"]
            expanded = result.get("explored_nodes", len(result.get("visited_order", [])))
            return build_path_response(path, exec_time, expanded)
        except ValueError:
            exec_time = (time.perf_counter() - t0) * 1000
            return {
                "found": False,
                "nodes_expanded": 0,
                "execution_time_ms": round(exec_time, 2)
            }

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
            return build_path_response(path, exec_time, expanded)
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

        while pq:
            f, g, curr = heapq.heappop(pq)
            if g > g_scores.get(curr, float('inf')):
                continue
            nodes_expanded += 1
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

    return build_path_response(path, exec_time, nodes_expanded)


def run_search_nearest_hospital(graph_mgr, start_id: int, algorithm: str = "astar", emergency_only: bool = True) -> Dict[str, Any]:
    """
    Dò đường tìm Bệnh Viện Gần Nhất trực tiếp trên mạng lưới đồ thị (Multi-Goal Search).
    Điểm đích KHÔNG cố định trước, thuật toán sẽ tự động lan tỏa từ vị trí xuất phát
    cho đến khi chạm trúng Bệnh Viện đầu tiên thỏa mãn tiêu chí tìm kiếm.
    """
    t0 = time.perf_counter()

    # Chuẩn hóa start_id
    if start_id not in graph_mgr.adj:
        node = graph_mgr.nodes.get(start_id)
        if node:
            nearest, _ = graph_mgr.find_nearest_road_node(node["lat"], node["lng"])
            if nearest:
                start_id = nearest["id"]

    if start_id not in graph_mgr.road_nodes:
        return {"found": False, "execution_time_ms": (time.perf_counter() - t0) * 1000}

    # Tập hợp các node ID của bệnh viện đích
    target_hospitals = graph_mgr.emergency_hospitals if (emergency_only and len(graph_mgr.emergency_hospitals) > 0) else graph_mgr.hospitals
    if not target_hospitals:
        return {"found": False, "message": "Không có bệnh viện nào trong hệ thống"}

    # Map nhanh từ node_id -> thông tin bệnh viện
    hospital_by_node = {h["node_id"]: h for h in target_hospitals}
    goal_node_set = set(hospital_by_node.keys())

    algo = algorithm.lower().strip()
    parent: Dict[int, Optional[int]] = {start_id: None}
    nodes_expanded = 0
    found_goal_id = None

    # Nếu start_id trùng ngay 1 bệnh viện
    if start_id in goal_node_set:
        start_node = graph_mgr.road_nodes[start_id]
        h_info = hospital_by_node[start_id]
        return {
            "found": True,
            "total_cost": 0.0,
            "total_distance_m": 0.0,
            "nodes_expanded": 1,
            "execution_time_ms": (time.perf_counter() - t0) * 1000,
            "path_coords": [[start_node["lat"], start_node["lng"]]],
            "path_nodes": [start_id],
            "destination_hospital": h_info
        }

    # Helper function build response
    def build_nearest_response(path_nodes, exec_time, expanded, dest_hospital):
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
            "path_nodes": path_nodes,
            "destination_hospital": dest_hospital
        }

    # Thuật toán 1: BFS (Tìm bệnh viện ít số bước nhảy / ngã rẽ nhất)
    if algo == "bfs":
        queue = deque([start_id])
        visited = {start_id}
        while queue:
            curr = queue.popleft()
            nodes_expanded += 1
            if curr in goal_node_set:
                found_goal_id = curr
                break
            for nbr in graph_mgr.adj.get(curr, {}):
                if nbr not in visited:
                    visited.add(nbr)
                    parent[nbr] = curr
                    queue.append(nbr)

    # Thuật toán 2: DFS (Tìm bệnh viện theo nhánh duyệt sâu đầu tiên)
    elif algo == "dfs":
        stack = [(start_id, None)]
        visited = set()
        while stack:
            curr, p = stack.pop()
            if curr in visited:
                continue
            visited.add(curr)
            parent[curr] = p
            nodes_expanded += 1
            if curr in goal_node_set:
                found_goal_id = curr
                break
            for nbr in graph_mgr.adj.get(curr, {}):
                if nbr not in visited:
                    stack.append((nbr, curr))

    # Thuật toán 3: DIJKSTRA (Tìm bệnh viện có quãng đường thực tế ngắn nhất)
    elif algo == "dijkstra":
        pq = [(0.0, start_id)]
        best_dist = {start_id: 0.0}
        while pq:
            d, curr = heapq.heappop(pq)
            if d > best_dist.get(curr, float('inf')):
                continue
            nodes_expanded += 1
            if curr in goal_node_set:
                found_goal_id = curr
                break
            for nbr, edge in graph_mgr.adj.get(curr, {}).items():
                new_d = d + edge[2]
                if new_d < best_dist.get(nbr, float('inf')):
                    best_dist[nbr] = new_d
                    parent[nbr] = curr
                    heapq.heappush(pq, (new_d, nbr))

    # Thuật toán 4 & 5: UCS / Multi-Goal A* (Tìm bệnh viện có chi phí tổng hợp thấp nhất)
    else:
        def h_multi(n_id: int) -> float:
            if algo == "ucs":
                return 0.0
            node = graph_mgr.road_nodes.get(n_id)
            if not node:
                return 0.0
            tree = graph_mgr.emergency_hospital_kdtree if (emergency_only and graph_mgr.emergency_hospital_kdtree is not None) else graph_mgr.hospital_kdtree
            if tree is not None:
                q = np.radians([node["lat"], node["lng"]])
                d_rad, _ = tree.query(q)
                return float(d_rad * 6371000.0) * 0.035
            return 0.0

        pq = [(h_multi(start_id), 0.0, start_id)]
        g_scores = {start_id: 0.0}

        while pq:
            f, g, curr = heapq.heappop(pq)
            if g > g_scores.get(curr, float('inf')):
                continue
            nodes_expanded += 1
            if curr in goal_node_set:
                found_goal_id = curr
                break
            for nbr, edge in graph_mgr.adj.get(curr, {}).items():
                tentative_g = g + edge[0]
                if tentative_g < g_scores.get(nbr, float('inf')):
                    g_scores[nbr] = tentative_g
                    parent[nbr] = curr
                    heapq.heappush(pq, (tentative_g + h_multi(nbr), tentative_g, nbr))

    exec_time = (time.perf_counter() - t0) * 1000

    if not found_goal_id:
        return {
            "found": False,
            "nodes_expanded": nodes_expanded,
            "execution_time_ms": round(exec_time, 2)
        }

    # Tái hiện đường đi
    path = []
    curr = found_goal_id
    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)
    path.reverse()

    dest_hospital = hospital_by_node.get(found_goal_id)
    return build_nearest_response(path, exec_time, nodes_expanded, dest_hospital)
