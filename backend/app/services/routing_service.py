import math
import os
import time
import heapq
from collections import deque
from typing import Any, Callable, Dict, List, Optional
import numpy as np

from backend.app.algorithms.graph_search.bfs.bfs import solve_bfs
from backend.app.algorithms.graph_search.astar import solve_astar
from backend.app.algorithms.graph_search.dijkstra import solve_dijkstra
from backend.app.algorithms.graph_search.ucs import solve_ucs
from backend.app.algorithms.graph_search.utils import get_edge_data
from backend.app.algorithms.optimization.hill_climbing import solve_hill_climbing
from backend.app.algorithms.optimization.held_karp import optimize_held_karp
from backend.app.algorithms.optimization.nearest_neighbor import optimize_nearest_neighbor
from backend.app.algorithms.optimization.genetic_algorithm import solve_genetic_algorithm
from backend.app.algorithms.optimization.simulated_annealing import solve_simulated_annealing
from backend.app.algorithms.graph_search.dfs import (
    solve_depth_limited_dfs,
    solve_dfs,
)
from backend.app.algorithms.graph_search.trace_history import SearchFailure, SearchTraceHistory
from backend.app.services.search_trace import build_search_trace


def is_render_environment() -> bool:
    """Return True if running in a Render cloud deployment or configured production environment."""
    return (
        os.getenv("RENDER", "").lower() in {"true", "1"}
        or os.getenv("IS_RENDER", "").lower() in {"true", "1"}
        or bool(os.getenv("RENDER_SERVICE_ID"))
        or bool(os.getenv("RENDER_INSTANCE_ID"))
        or os.getenv("APP_ENV", "").lower() in {"production", "prod", "render"}
    )

def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000.0
    r_lat1, r_lng1 = math.radians(lat1), math.radians(lng1)
    r_lat2, r_lng2 = math.radians(lat2), math.radians(lng2)
    dlat = r_lat2 - r_lat1
    dlng = r_lng2 - r_lng1
    a = math.sin(dlat/2)**2 + math.cos(r_lat1)*math.cos(r_lat2)*math.sin(dlng/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_edge_cost_function(criterion: str):
    """Return an edge cost function based on the selected criterion."""
    def edge_cost_fn(graph, source, target, _cost_profile=None) -> float:
        edge = get_edge_data(graph, source, target)
        if isinstance(edge, dict):
            if criterion == "distance":
                return float(edge.get("distance", edge.get("weight", 1.0)))
            elif criterion == "hops":
                return 1.0
            elif criterion == "time":
                return float(edge.get("estimated_time", edge.get("time", 1.0)))
            else:
                return float(edge.get("total_cost", edge.get("weight", 1.0)))
        
        if isinstance(edge, (list, tuple)):
            if criterion == "distance":
                return float(edge[2]) if len(edge) > 2 else 1.0
            elif criterion == "hops":
                return 1.0
            elif criterion == "time":
                return float(edge[3]) if len(edge) > 3 else (float(edge[2]) / (40000 / 60) if len(edge) > 2 else 1.0)
            else:
                return float(edge[0]) if len(edge) > 0 else 1.0
        
        return float(edge)
    return edge_cost_fn



def build_priority_frontier_snapshot(
    current_node: int,
    current_cost: float,
    current_priority: float,
    priority_queue: List[tuple],
    best_scores: Dict[int, float],
    heuristic: Optional[Callable[[int], float]] = None,
    max_items: int = 24,
) -> List[Dict[str, Any]]:

    """Build one shared priority-queue snapshot for UCS, A*, and Dijkstra."""

    def format_item(node_id: int, cost: float, priority: float) -> Dict[str, Any]:
        item: Dict[str, Any] = {
            "node_id": node_id,
            "g": round(cost, 2),
            "f": round(priority, 2),
        }
        if heuristic is not None:
            item["h"] = round(heuristic(node_id), 2)
        return item

    snapshot = [format_item(current_node, current_cost, current_priority)]
    included_nodes = {current_node}
    candidates = (
        heapq.nsmallest(max_items * 3, priority_queue)
        if len(priority_queue) > max_items * 3
        else sorted(priority_queue)
    )
    for entry in candidates:
        if len(entry) == 2:
            priority, node_id = entry
            cost = priority
        else:
            priority, cost, node_id = entry
        if cost != best_scores.get(node_id) or node_id in included_nodes:
            continue
        included_nodes.add(node_id)
        snapshot.append(format_item(node_id, cost, priority))
        if len(snapshot) >= max_items:
            break
    return snapshot



def run_search(graph_mgr, start_id: int, goal_id: int, algorithm: str, criterion: str = "cost") -> Dict[str, Any]:
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
        """Return the final route and replayable trace in one response."""

        response = build_path_response(path_nodes, exec_time, expanded)
        response["algorithm"] = algo
        response["search_trace"] = build_search_trace(
            graph_mgr,
            trace_result,
            algo,
        )
        return response

    if start_id == goal_id:
        trace_history = SearchTraceHistory()
        trace_history.record_expansion(start_id, [start_id])
        return build_success_response(
            [start_id],
            (time.perf_counter() - t0) * 1000,
            trace_history.explored_nodes,
            trace_history.as_result_fields(),
        )

    if algo == "bfs":
        try:
            result = solve_bfs(graph_mgr.adj, start_id, goal_id)
        except SearchFailure as error:
            result = error.result
        exec_time = (time.perf_counter() - t0) * 1000
        
        if not result.get("found", True) or not result.get("path"):
            response = {
                "found": False,
                "algorithm": "bfs",
                "nodes_expanded": result.get("explored_nodes", 0),
                "execution_time_ms": round(exec_time, 2),
                "message": result.get(
                    "message",
                    f"No route found from '{start_id}' to '{goal_id}'."
                )
            }
            response["search_trace"] = build_search_trace(
                graph_mgr, result, "bfs"
            )
            return response
            
        # BFS was successful
        path = result["path"]
        expanded = result.get("explored_nodes", len(result.get("visited_order", [])))
        response = build_success_response(path, exec_time, expanded, result)
        response["explanation_data"] = result.get("explanation_data", {})
        response["hop_count"] = result.get("hop_count")
        response["is_optimal"] = result.get("is_optimal")
        return response

    elif algo in {"dfs", "dls", "bounded_dfs", "dfs_limited"}:
        try:
            # If running on Render cloud deployment (or requested bounded dfs), limit to 3000 node expansions
            # Otherwise in local environment, use standard unconstrained DFS (solve_dfs)
            is_cloud = is_render_environment() or algo in {"dls", "bounded_dfs", "dfs_limited"}
            if is_cloud:
                result = solve_depth_limited_dfs(
                    graph_mgr.adj, start_id, goal_id, max_expansions=3000
                )
            else:
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
        except SearchFailure as error:
            exec_time = (time.perf_counter() - t0) * 1000
            return {
                "found": False,
                "algorithm": "dfs",
                "nodes_expanded": error.result.get("explored_nodes", 0),
                "execution_time_ms": round(exec_time, 2),
                "message": str(error),
                "search_trace": build_search_trace(
                    graph_mgr, error.result, "dfs"
                ),
            }


    elif algo in {"astar", "ucs", "dijkstra", "hill_climbing", "hill-climbing"}:
        def h(n_id: int) -> float:
            if criterion == "hops":
                return 0.0
            node = graph_mgr.road_nodes.get(n_id)
            if not node:
                return 0.0
            distance = haversine(
                node["lat"], node["lng"], goal_node["lat"], goal_node["lng"]
            )
            
            if algo.startswith("hill"):
                return distance
            
            if criterion == "distance":
                return distance
            elif criterion == "time":
                return distance / (40000 / 60) # fallback speed
            else: # cost
                return distance * 0.00135287

        try:
            custom_edge_cost = get_edge_cost_function(criterion)
            if algo.startswith("hill"):
                result = solve_hill_climbing (graph_mgr.adj, start_id, goal_id,
                    lambda node_id, _goal_id: h(node_id),
                    edge_cost=custom_edge_cost
                )
            elif algo == "ucs":
                result = solve_ucs(graph_mgr.adj, start_id, goal_id, edge_cost=custom_edge_cost)
            elif algo == "dijkstra":
                result = solve_dijkstra(graph_mgr.adj, start_id, goal_id, edge_cost=custom_edge_cost)
            else:
                result = solve_astar(graph_mgr.adj, start_id, goal_id,
                    lambda node_id, _goal_id: h(node_id),
                    edge_cost=custom_edge_cost
                )
        except SearchFailure as error:
            return {
                "found": False,
                "algorithm": algo,
                "nodes_expanded": error.result.get("explored_nodes", 0),
                "execution_time_ms": round((time.perf_counter() - t0) * 1000, 2),
                "message": str(error),
                "search_trace": build_search_trace(
                    graph_mgr,
                    error.result,
                    algo,
                ),
            }
        except ValueError as error:
            return {
                "found": False,
                "algorithm": algo,
                "nodes_expanded": 0,
                "execution_time_ms": round((time.perf_counter() - t0) * 1000, 2),
                "message": str(error),
            }

        exec_time = (time.perf_counter() - t0) * 1000
        response = build_success_response(
            result["path"],
            exec_time,
            result["explored_nodes"],
            result,
        )
        response["explanation_data"] = result.get("explanation_data", {})
        response["is_optimal"] = result.get("is_optimal")
        return response

    else:
        return {
            "found": False,
            "algorithm": algo,
            "nodes_expanded": 0,
            "execution_time_ms": round((time.perf_counter() - t0) * 1000, 2),
            "message": f"Unsupported search algorithm: '{algorithm}'.",
        }

    raise AssertionError("Search dispatch reached an unexpected state.")


def run_multi_location_search(
    graph_mgr,
    start_id: int,
    waypoint_ids: List[int],
    goal_id: int,
    route_algorithm: str = "astar",
    optimization_method: str = "nearest_neighbor",
    criterion: str = "cost",
) -> Dict[str, Any]:
    """Optimize waypoint order and return every selected route segment."""

    started_at = time.perf_counter()
    waypoints = list(dict.fromkeys(waypoint_ids))
    if start_id in waypoints or goal_id in waypoints:
        waypoints = [
            node_id
            for node_id in waypoints
            if node_id not in {start_id, goal_id}
        ]
    if len(waypoints) > 10:
        return {
            "found": False,
            "message": "Multi-location optimization supports at most 10 waypoints.",
        }

    pair_results: Dict[tuple, Dict[str, Any]] = {}
    pair_costs: Dict[tuple, float] = {}
    sources = [start_id, *waypoints]
    targets = [*waypoints, goal_id]
    for source in sources:
        for target in targets:
            result = run_search(graph_mgr, source, target, route_algorithm, criterion)
            pair_results[(source, target)] = result
            pair_costs[(source, target)] = (
                _route_objective(result, criterion)
                if result.get("found")
                else float("inf")
            )

    method = optimization_method.lower().strip().replace("-", "_")
    try:
        if method == "nearest_neighbor":
            optimized = optimize_nearest_neighbor(
                start_id,
                waypoints,
                goal_id,
                pair_costs,
            )
        elif method == "held_karp":
            optimized = optimize_held_karp(
                start_id,
                waypoints,
                goal_id,
                pair_costs,
            )
        elif method in ("genetic_algorithm", "simulated_annealing"):
            locations = [start_id, *waypoints, goal_id]
            distance_matrix = {loc: {} for loc in locations}
            for (src, tgt), cost in pair_costs.items():
                if src not in distance_matrix:
                    distance_matrix[src] = {}
                distance_matrix[src][tgt] = cost

            if method == "genetic_algorithm":
                optimized = solve_genetic_algorithm(
                    locations, distance_matrix, start_id, goal_id
                )
            else:
                optimized = solve_simulated_annealing(
                    locations, distance_matrix, start_id, goal_id
                )
        else:
            return {
                "found": False,
                "message": f"Unsupported optimization method: '{optimization_method}'.",
            }
    except ValueError as error:
        return {
            "found": False,
            "message": str(error),
            "optimization_method": method,
        }

    visiting_order = optimized["visiting_order"]
    segments = []
    merged_path_nodes = []
    merged_path_coords = []
    total_cost = 0.0
    total_distance = 0.0
    total_expanded = 0
    for index, (source, target) in enumerate(
        zip(visiting_order, visiting_order[1:])
    ):
        result = pair_results[(source, target)]
        if not result.get("found"):
            return {
                "found": False,
                "message": result.get(
                    "message",
                    f"No route from '{source}' to '{target}'.",
                ),
            }
        path_nodes = result.get("path_nodes", [])
        path_coords = result.get("path_coords", [])
        merged_path_nodes.extend(path_nodes if index == 0 else path_nodes[1:])
        merged_path_coords.extend(path_coords if index == 0 else path_coords[1:])
        total_cost += float(result.get("total_cost", 0.0))
        total_distance += float(result.get("total_distance_m", 0.0))
        total_expanded += int(result.get("nodes_expanded", 0))
        segments.append({"start": source, "goal": target, "result": result})

    original_order = [start_id, *waypoints, goal_id]
    original_objective = sum(
        pair_costs.get((source, target), float("inf"))
        for source, target in zip(original_order, original_order[1:])
    )
    original_objective_value = (
        round(float(original_objective), 6)
        if math.isfinite(original_objective)
        else None
    )
    return {
        "found": True,
        "route_algorithm": route_algorithm,
        "optimization_method": method,
        "criterion": criterion,
        "order_is_optimal": optimized["is_optimal"],
        "is_optimal": optimized["is_optimal"],
        "visiting_order": visiting_order,
        "ordered_waypoints": visiting_order[1:-1],
        "objective_cost": round(float(optimized["objective_cost"]), 6),
        "original_order": original_order,
        "original_objective_cost": original_objective_value,
        "segments": segments,
        "path_nodes": merged_path_nodes,
        "path_coords": merged_path_coords,
        "total_cost": round(total_cost, 2),
        "total_distance_m": round(total_distance, 2),
        "nodes_expanded": total_expanded,
        "execution_time_ms": round(
            (time.perf_counter() - started_at) * 1000,
            2,
        ),
    }


def _route_objective(result: Dict[str, Any], criterion: str) -> float:
    """Return the pairwise score used by the ordering algorithm."""

    normalized = criterion.lower().strip()
    if normalized == "distance":
        return float(result.get("total_distance_m", float("inf")))
    if normalized == "hops":
        return float(max(0, len(result.get("path_nodes", [])) - 1))
    # The current dataset folds estimated travel time and congestion into cost.
    return float(result.get("total_cost", float("inf")))


def run_search_nearest_hospital(graph_mgr, start_id: int, algorithm: str = "astar", emergency_only: bool = True, criterion: str = "cost") -> Dict[str, Any]:
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
    trace_history = SearchTraceHistory()

    goal_distance_cache: Dict[int, float] = {}

    def nearest_goal_distance(node_id: int) -> float:
        """Estimate straight-line distance to the closest candidate hospital."""
        if node_id in goal_distance_cache:
            return goal_distance_cache[node_id]

        node = graph_mgr.road_nodes.get(node_id)
        if not node:
            goal_distance_cache[node_id] = 0.0
            return 0.0
        tree = (
            graph_mgr.emergency_hospital_kdtree
            if emergency_only and graph_mgr.emergency_hospital_kdtree is not None
            else graph_mgr.hospital_kdtree
        )
        if tree is not None:
            query = np.radians([node["lat"], node["lng"]])
            distance_radians, _ = tree.query(query)
            res = float(distance_radians * 6371000.0)
            goal_distance_cache[node_id] = res
            return res


        distances = []
        for hospital in target_hospitals:
            target = graph_mgr.road_nodes.get(hospital["node_id"], hospital)
            if "lat" in target and "lng" in target:
                distances.append(
                    haversine(
                        node["lat"],
                        node["lng"],
                        target["lat"],
                        target["lng"],
                    )
                )
        return min(distances, default=0.0)

    # Nếu start_id trùng ngay 1 bệnh viện
    if start_id in goal_node_set:
        start_node = graph_mgr.road_nodes[start_id]
        h_info = hospital_by_node[start_id]
        trace_history.record_expansion(start_id, [start_id])
        return {
            "found": True,
            "algorithm": algo,
            "total_cost": 0.0,
            "total_distance_m": 0.0,
            "nodes_expanded": trace_history.explored_nodes,
            "execution_time_ms": (time.perf_counter() - t0) * 1000,
            "path_coords": [[start_node["lat"], start_node["lng"]]],
            "path_nodes": [start_id],
            "destination_hospital": h_info,
            "search_trace": build_search_trace(
                graph_mgr,
                trace_history.as_result_fields(),
                algo,
            ),
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

        response = {
            "found": True,
            "algorithm": algo,
            "total_cost": round(total_cost, 2),
            "total_distance_m": round(total_dist, 2),
            "nodes_expanded": expanded,
            "execution_time_ms": round(exec_time, 2),
            "path_coords": path_coords,
            "path_nodes": path_nodes,
            "destination_hospital": dest_hospital
        }
        response["search_trace"] = build_search_trace(
            graph_mgr,
            trace_history.as_result_fields(),
            algo,
        )
        return response

    # Thuật toán 1: BFS (Tìm bệnh viện ít số bước nhảy / ngã rẽ nhất)
    if algo == "bfs":
        queue = deque([start_id])
        visited = {start_id}
        while queue:
            curr = queue[0]
            trace_history.record_expansion(curr, queue)
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
            frontier_preview = [node for node, _ in stack[:4999]] + [curr]
            trace_history.record_expansion(
                curr,
                frontier_preview,
            )
            visited.add(curr)
            parent[curr] = p
            nodes_expanded += 1
            if curr in goal_node_set:
                found_goal_id = curr
                break
            if nodes_expanded >= 5000:
                break
            for nbr in graph_mgr.adj.get(curr, {}):
                if nbr not in visited:
                    stack.append((nbr, curr))


    elif algo in {"hill_climbing", "hill-climbing"}:
        current = start_id
        visited = {current}
        while True:
            nodes_expanded += 1
            if current in goal_node_set:
                trace_history.record_expansion(current, [])
                found_goal_id = current
                break

            candidates = [
                neighbor
                for neighbor in graph_mgr.adj.get(current, {})
                if neighbor not in visited
            ]
            ranked = sorted(
                (nearest_goal_distance(node_id), repr(node_id), node_id)
                for node_id in candidates
            )
            current_h = nearest_goal_distance(current)
            can_advance = bool(ranked and ranked[0][0] < current_h)
            selected = ranked[0][2] if can_advance else None
            trace_history.record_expansion(
                current,
                [
                    {
                        "node_id": node_id,
                        "h": round(score, 6),
                        "priority": round(score, 6),
                        "selected": bool(node_id == selected),
                    }
                    for score, _key, node_id in ranked

                ],
            )
            if selected is None:
                break
            parent[selected] = current
            current = selected
            visited.add(current)

    # Thuật toán 3: DIJKSTRA (Tìm bệnh viện có quãng đường/tiêu chí thực tế ngắn nhất)
    elif algo == "dijkstra":
        custom_edge_cost = get_edge_cost_function(criterion)
        pq = [(0.0, start_id)]
        best_dist = {start_id: 0.0}
        while pq:
            d, curr = heapq.heappop(pq)
            if d > best_dist.get(curr, float('inf')):
                continue
            nodes_expanded += 1
            if nodes_expanded < 5000:
                trace_history.record_expansion(
                    curr,
                    build_priority_frontier_snapshot(
                        curr,
                        d,
                        d,
                        pq,
                        best_dist,
                        max_items=24,
                    ),
                )
            else:
                trace_history.record_expansion(curr, [])
            if curr in goal_node_set:
                found_goal_id = curr
                break
            for nbr, edge in graph_mgr.adj.get(curr, {}).items():
                cost_val = custom_edge_cost(graph_mgr.adj, curr, nbr)
                new_d = d + cost_val
                if new_d < best_dist.get(nbr, float('inf')):
                    best_dist[nbr] = new_d
                    parent[nbr] = curr
                    heapq.heappush(pq, (new_d, nbr))

    # Thuật toán 4 & 5: UCS / Multi-Goal A* (Tìm bệnh viện có chi phí tổng hợp thấp nhất)
    else:
        custom_edge_cost = get_edge_cost_function(criterion)
        def h_multi(n_id: int) -> float:
            if algo == "ucs" or criterion == "hops":
                return 0.0
            dist = nearest_goal_distance(n_id)
            if criterion == "distance":
                return dist
            elif criterion == "time":
                return dist / (40000 / 60)
            else:
                return dist * 0.00135287

        pq = [(h_multi(start_id), 0.0, start_id)]
        g_scores = {start_id: 0.0}

        while pq:
            f, g, curr = heapq.heappop(pq)
            if g > g_scores.get(curr, float('inf')):
                continue
            nodes_expanded += 1
            if nodes_expanded < 5000:
                trace_history.record_expansion(
                    curr,
                    build_priority_frontier_snapshot(
                        curr,
                        g,
                        f,
                        pq,
                        g_scores,
                        h_multi,
                        max_items=24,
                    ),
                )
            else:
                trace_history.record_expansion(curr, [])

            if curr in goal_node_set:
                found_goal_id = curr
                break
            for nbr, edge in graph_mgr.adj.get(curr, {}).items():
                cost_val = custom_edge_cost(graph_mgr.adj, curr, nbr)
                tentative_g = g + cost_val
                if tentative_g < g_scores.get(nbr, float('inf')):
                    g_scores[nbr] = tentative_g
                    parent[nbr] = curr
                    heapq.heappush(pq, (tentative_g + h_multi(nbr), tentative_g, nbr))

    exec_time = (time.perf_counter() - t0) * 1000

    if not found_goal_id:
        return {
            "found": False,
            "algorithm": algo,
            "nodes_expanded": nodes_expanded,
            "execution_time_ms": round(exec_time, 2),
            "search_trace": build_search_trace(
                graph_mgr,
                trace_history.as_result_fields(),
                algo,
            ),
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
