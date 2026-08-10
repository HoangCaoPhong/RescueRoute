import os
import gc
import time
import math
import heapq
from datetime import datetime
from collections import deque
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ==========================================
# 1. Đường dẫn tệp & Dữ liệu
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.html")
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/processed"))

# ==========================================
import sys
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, "../scripts")))
import dataset_2_graph

# ==========================================
# 3. Quản lý Đồ thị & Dữ liệu trong RAM (Tối ưu cho 512MB)
# ==========================================
class GraphManager:
    def __init__(self):
        self.road_nodes = {}
        self.edges_cache = []
        self.adj = None
        self.kdtree = None
        self.road_node_ids_array = np.array([])
        self.hospitals = []
        self.pois = []
        self.dynamic_edges_count = 0
        self.ambulance_lat = 10.7735
        self.ambulance_lng = 106.6980
        self.is_loaded = False
        
        # Thêm node ảo để tương thích với các API cũ nều cần
        self.nodes = {}

    def load_data(self):
        if self.is_loaded: return
        t0 = time.perf_counter()
        
        df_nodes, df_train, df_base = dataset_2_graph.read()
        
        needed_road_nodes = set(df_base['s_node_id']).union(set(df_base['e_node_id']))
        for _, row in df_nodes[df_nodes['_id'].isin(needed_road_nodes)].iterrows():
            n_id = int(row["_id"])
            p_name = str(row["poi_name"]) if pd.notna(row["poi_name"]) and str(row["poi_name"]) != "None" else None
            self.road_nodes[n_id] = {
                "id": n_id, "lat": float(row["lat"]), "lng": float(row["long"]), "poi_name": p_name
            }
            
        self.adj = dataset_2_graph.build_graph(df_base, df_train)
        
        congested_edges = []
        normal_edges = []
        for u in self.adj:
            for v, edge_data in self.adj[u].items():
                edge_id = f"{u}_{v}"
                u_node = self.road_nodes.get(u)
                v_node = self.road_nodes.get(v)
                if u_node and v_node:
                    item = {
                        "edge_id": edge_id, "name": f"Đoạn {u}-{v}", "distance": edge_data[2],
                        "congestion_level": edge_data[1], "congestion_factor": 1.0,
                        "current_cost": round(edge_data[0], 2), "base_cost": round(edge_data[0], 2),
                        "u_lat": u_node["lat"], "u_lng": u_node["lng"], "v_lat": v_node["lat"], "v_lng": v_node["lng"]
                    }
                    if item["congestion_level"] >= 2: congested_edges.append(item)
                    else: normal_edges.append(item)
        self.edges_cache = congested_edges + normal_edges
        
        road_ids = []
        road_coords = []
        for n_id, n_data in self.road_nodes.items():
            road_ids.append(n_id)
            road_coords.append((n_data["lat"], n_data["lng"]))

        self.road_node_ids_array = np.array(road_ids)
        if len(road_coords) > 0:
            coords_rad = np.radians(np.array(road_coords))
            self.kdtree = cKDTree(coords_rad)
            
        hospitals_list = []
        pois_list = []
        for _, row in df_nodes.iterrows():
            p_name = str(row["poi_name"]) if pd.notna(row["poi_name"]) and str(row["poi_name"]) != "None" else None
            p_label = str(row["poi_label"]) if pd.notna(row["poi_label"]) else "Background"
            lat = float(row["lat"])
            lng = float(row["long"])
            n_id = int(row["_id"])
            is_hospital = ((p_label.lower() == "hospital") or (p_name and any(kw in p_name.lower() for kw in ["bệnh viện", "benh vien", "hospital", "phòng khám", "trạm y tế", "clinic", "y tế"])))
            if is_hospital and p_name:
                nearest_road_node, dist_m = self.find_nearest_road_node(lat, lng)
                target_node_id = nearest_road_node["id"] if nearest_road_node else n_id
                hospitals_list.append({
                    "node_id": target_node_id, "poi_node_id": n_id, "name": p_name,
                    "type": p_label if p_label != "Background" else "Bệnh viện / Cơ sở Y tế", "lat": lat, "lng": lng, "is_hospital": True
                })
            elif p_name or p_label != "Background":
                pois_list.append({
                    "node_id": n_id, "poi_node_id": n_id, "name": p_name,
                    "type": p_label, "lat": lat, "lng": lng, "is_hospital": False
                })
        self.hospitals = hospitals_list
        self.pois = pois_list
        self.nodes = self.road_nodes # Alias cho tương thích
        self.is_loaded = True
        
    def find_nearest_road_node(self, lat: float, lng: float) -> Tuple[Optional[Dict[str, Any]], float]:
        if self.kdtree is None or len(self.road_node_ids_array) == 0:
            return None, 0.0
        query_pt = np.radians([lat, lng])
        dist_rad, idx = self.kdtree.query(query_pt)
        dist_m = float(dist_rad * 6371000.0)
        nearest_id = int(self.road_node_ids_array[idx])
        return self.road_nodes.get(nearest_id), round(dist_m, 1)

# Nạp dữ liệu ngay khi khởi động
graph_mgr = GraphManager()
graph_mgr.load_data()

# ==========================================
# 3. Khởi tạo FastAPI App & Middleware
# ==========================================
app = FastAPI(
    title="RescueRoute Demo",
    description="Backend Demo Tìm đường Xe Cấp Cứu",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 4. Request Schemas
# ==========================================
class AmbulanceLocationRequest(BaseModel):
    lat: float
    lng: float

class RouteRequest(BaseModel):
    start_node_id: Optional[int] = None
    goal_node_id: int
    algorithm: str = "astar"

class CongestionRequest(BaseModel):
    edge_id: str
    congestion_level: int

# ==========================================
# 5. Thuật toán Tìm đường trên Đồ thị
# ==========================================
def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000.0
    r_lat1, r_lng1 = math.radians(lat1), math.radians(lng1)
    r_lat2, r_lng2 = math.radians(lat2), math.radians(lng2)
    dlat = r_lat2 - r_lat1
    dlng = r_lng2 - r_lng1
    a = math.sin(dlat/2)**2 + math.cos(r_lat1)*math.cos(r_lat2)*math.sin(dlng/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def run_search(start_id: int, goal_id: int, algorithm: str) -> Dict[str, Any]:
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

    if algo == "bfs":
        queue = deque([start_id])
        visited = {start_id}
        while queue:
            curr = queue.popleft()
            nodes_expanded += 1
            if curr == goal_id:
                found = True
                break
            for nbr in graph_mgr.adj.get(curr, {}):
                if nbr not in visited:
                    visited.add(nbr)
                    parent[nbr] = curr
                    queue.append(nbr)

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

    # Tái hiện đường đi
    path = []
    curr = goal_id
    while curr is not None:
        path.append(curr)
        curr = parent.get(curr)
    path.reverse()

    total_cost = 0.0
    total_dist = 0.0
    path_coords = []
    for i in range(len(path)):
        node = graph_mgr.road_nodes.get(path[i]) or graph_mgr.nodes.get(path[i])
        if node:
            path_coords.append([node["lat"], node["lng"]])
        if i < len(path) - 1:
            edge = graph_mgr.adj.get(path[i], {}).get(path[i+1])
            if edge:
                total_cost += edge[0]
                total_dist += edge[2]

    return {
        "found": True,
        "total_cost": round(total_cost, 2),
        "total_distance_m": round(total_dist, 2),
        "nodes_expanded": nodes_expanded,
        "execution_time_ms": round(exec_time, 2),
        "path_coords": path_coords,
        "path_nodes": path
    }

# ==========================================
# 6. Các API Endpoints
# ==========================================
@app.get("/")
@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard():
    """Mở trực tiếp giao diện Dashboard bản đồ"""
    if os.path.exists(DASHBOARD_FILE):
        return FileResponse(DASHBOARD_FILE)
    return {"message": "dashboard.html không tìm thấy"}

@app.get("/api/health")
@app.get("/api/v1/health")
@app.get("/health")
async def health():
    """Kiểm tra sức khỏe hệ thống và số node/edge trên RAM"""
    t0 = time.perf_counter()
    latency = (time.perf_counter() - t0) * 1000
    return {
        "status": "ok",
        "env": "development",
        "version": "1.0.0",
        "latency_ms": round(latency, 2),
        "nodes_count": len(graph_mgr.road_nodes),
        "edges_count": len(graph_mgr.edges_cache),
        "dynamic_edges_count": graph_mgr.dynamic_edges_count
    }

@app.get("/api/nodes")
@app.get("/api/v1/nodes")
async def get_nodes(poi_type: Optional[str] = Query("hospital"), limit: int = Query(570000)):
    """Hiển thị danh sách các bệnh viện/trạm y tế và POI trên bản đồ"""
    if not poi_type or poi_type == "hospital":
        return graph_mgr.hospitals[:limit]
    if poi_type == "all":
        return (graph_mgr.hospitals + graph_mgr.pois)[:limit]
    return [p for p in graph_mgr.pois if p["type"] and poi_type.lower() in p["type"].lower()][:limit]

@app.get("/api/edges")
@app.get("/api/v1/edges")
async def get_edges(limit: int = Query(2000)):
    """Hiển thị mạng lưới các tuyến đường và mức độ kẹt xe"""
    return graph_mgr.edges_cache[:limit]

@app.get("/api/ambulance/location")
@app.get("/api/v1/ambulance/location")
async def get_ambulance_location():
    """Lấy vị trí xe cấp cứu và ánh xạ sang node gần nhất"""
    nearest_node, dist_m = graph_mgr.find_nearest_road_node(graph_mgr.ambulance_lat, graph_mgr.ambulance_lng)
    mapped = {}
    if nearest_node:
        mapped = {
            "nearest_node_id": nearest_node["id"],
            "nearest_node_name": nearest_node["poi_name"] or f"Nút giao #{nearest_node['id']}",
            "distance_meters": dist_m
        }
    return {
        "lat": graph_mgr.ambulance_lat,
        "lng": graph_mgr.ambulance_lng,
        "mapped_nearest_node": mapped
    }

@app.post("/api/ambulance/location")
@app.post("/api/v1/ambulance/location")
async def update_ambulance_location(body: AmbulanceLocationRequest):
    """Cập nhật vị trí GPS xe cấp cứu khi click hoặc nhận từ GPS"""
    graph_mgr.ambulance_lat = body.lat
    graph_mgr.ambulance_lng = body.lng
    nearest_node, dist_m = graph_mgr.find_nearest_road_node(body.lat, body.lng)
    mapped = {}
    if nearest_node:
        mapped = {
            "nearest_node_id": nearest_node["id"],
            "nearest_node_name": nearest_node["poi_name"] or f"Nút giao #{nearest_node['id']}",
            "distance_meters": dist_m
        }
    return {
        "status": "success",
        "current_gps": {
            "lat": graph_mgr.ambulance_lat,
            "lng": graph_mgr.ambulance_lng,
            "mapped_nearest_node": mapped
        }
    }

@app.post("/api/route")
@app.post("/api/v1/route")
async def calculate_route(body: RouteRequest):
    """Tìm đường tối ưu (A*, Dijkstra, BFS, DFS, UCS) và vẽ tuyến đường"""
    start_id = body.start_node_id
    if start_id is None:
        nearest_node, _ = graph_mgr.find_nearest_road_node(graph_mgr.ambulance_lat, graph_mgr.ambulance_lng)
        start_id = nearest_node["id"] if nearest_node else list(graph_mgr.road_nodes.keys())[0]

    return run_search(start_id, body.goal_node_id, body.algorithm)

@app.post("/api/edges/congestion")
@app.post("/api/v1/edges/congestion")
async def update_congestion(body: CongestionRequest):
    """Mô phỏng cập nhật tình trạng kẹt xe trên đoạn đường"""
    try:
        u_str, v_str = body.edge_id.split('_')
        u, v = int(u_str), int(v_str)
    except:
        raise HTTPException(status_code=400, detail="Invalid edge_id")
        
    edge = graph_mgr.adj.get(u, {}).get(v)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge không tồn tại")

    edge[1] = body.congestion_level
    edge[0] = edge[0] * (1.0 + 0.5 * (body.congestion_level - 1))

    for item in graph_mgr.edges_cache:
        if item["edge_id"] == body.edge_id:
            item["congestion_level"] = body.congestion_level
            item["current_cost"] = edge[0]
            break

    return {
        "status": "updated",
        "edge_id": body.edge_id,
        "congestion_level": body.congestion_level
    }
