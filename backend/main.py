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
# 2. Hàm Tiện Ích & Chi Phí Giao Thông
# ==========================================
def calc_cost(time_val: float, congestion: float, risk: float, parameters: Tuple[float, float, float] = (0.648, 0.23, 0.122)) -> float:
    """Tính chi phí đoạn đường: cost = 0.648 * time + 0.23 * (congestion^2) + 0.122 * (risk^2)"""
    return parameters[0] * time_val + parameters[1] * (congestion ** 2) + parameters[2] * (risk ** 2)

def map_congestion_to_level(factor: float) -> int:
    """Chuyển đổi congestion_factor sang cấp độ kẹt xe 1 - 5 cho bản đồ nhiệt"""
    if factor < 1.4:
        return 1
    elif factor < 2.0:
        return 2
    elif factor < 3.2:
        return 3
    elif factor < 5.5:
        return 4
    else:
        return 5

def get_nearby_periods() -> List[str]:
    """Lấy danh sách các khung giờ (period) gần thời điểm hiện tại"""
    current_time = datetime.now()
    hour = current_time.hour
    minute = current_time.minute
    
    if minute < 15:
        curr_slot = (hour, 0)
    elif minute < 45:
        curr_slot = (hour, 30)
    else:
        curr_slot = ((hour + 1) % 24, 0)
        
    slots = []
    # prev slot
    if curr_slot[1] == 0:
        slots.append(((curr_slot[0] - 1) % 24, 30))
    else:
        slots.append((curr_slot[0], 0))
        
    # curr slot
    slots.append(curr_slot)
    
    # next slot
    if curr_slot[1] == 0:
        slots.append((curr_slot[0], 30))
    else:
        slots.append(((curr_slot[0] + 1) % 24, 0))
        
    periods = [f"period_{h}_{m:02d}" for h, m in slots]
    return periods

# ==========================================
# 3. Quản lý Đồ thị & Dữ liệu trong RAM (Tối ưu cho 512MB)
# ==========================================
class GraphManager:
    def __init__(self):
        self.road_nodes: Dict[int, Dict[str, Any]] = {}  # Chỉ chứa 52k node thuộc mạng lưới giao thông
        self.edges: Dict[str, Dict[str, Any]] = {}
        self.adj: Dict[int, Dict[int, Dict[str, Any]]] = {}
        self.kdtree: Optional[cKDTree] = None
        self.road_node_ids_array: np.ndarray = np.array([])
        self.hospitals: List[Dict[str, Any]] = []
        self.edges_cache: List[Dict[str, Any]] = []
        self.dynamic_edges_count: int = 0
        self.ambulance_lat: float = 10.7735
        self.ambulance_lng: float = 106.6980
        self.is_loaded: bool = False

    def load_data(self):
        if self.is_loaded:
            return

        nodes_csv = os.path.join(DATA_DIR, "nodes_with_poi_labels.csv")
        edges_csv = os.path.join(DATA_DIR, "base_segments.csv")
        train_csv = os.path.join(DATA_DIR, "processed_train.csv")

        if not os.path.exists(nodes_csv) or not os.path.exists(edges_csv):
            print(f"[Cảnh báo] Không tìm thấy dữ liệu trong {DATA_DIR}")
            return

        print(f"[INFO] Dang nap du lieu toi uu RAM tu {DATA_DIR}...")
        t0 = time.perf_counter()

        # 1. Đọc base_segments.csv trước để xác định tập các nút giao thông thực tế
        df_edges = pd.read_csv(edges_csv)
        needed_road_nodes = set(df_edges['s_node_id']).union(set(df_edges['e_node_id']))

        # 2. Đọc nodes_with_poi_labels.csv: CHỈ nạp các nút giao thông và POI bệnh viện (Tiết kiệm >200MB RAM)
        df_nodes = pd.read_csv(nodes_csv)
        
        # Lọc nhanh road nodes
        for _, row in df_nodes[df_nodes['_id'].isin(needed_road_nodes)].iterrows():
            n_id = int(row["_id"])
            p_name = str(row["poi_name"]) if pd.notna(row["poi_name"]) and str(row["poi_name"]) != "None" else None
            self.road_nodes[n_id] = {
                "id": n_id,
                "lat": float(row["lat"]),
                "lng": float(row["long"]),
                "poi_name": p_name
            }

        # 3. Xây dựng Mạng lưới Giao thông Full Map từ base_segments.csv
        for _, row in df_edges.iterrows():
            u = int(row["s_node_id"])
            v = int(row["e_node_id"])
            length = float(row["length"])
            b_time = float(row["base_time"])
            b_cost = float(row["base_cost"])
            edge_id = f"{u}_{v}"

            if u not in self.adj:
                self.adj[u] = {}
            if v not in self.adj:
                self.adj[v] = {}

            edge_data_forward = {
                "edge_id": edge_id,
                "s_node_id": u,
                "e_node_id": v,
                "length": length,
                "base_time": b_time,
                "base_cost": b_cost,
                "current_cost": b_cost,
                "congestion_level": 1,
                "congestion_factor": 1.0,
                "risk_factor": 1.0,
                "name": f"Đoạn {u} -> {v}"
            }
            self.edges[edge_id] = edge_data_forward
            self.adj[u][v] = edge_data_forward

            # Hỗ trợ lưu thông 2 chiều cho xe cấp cứu ưu tiên
            rev_edge_id = f"{v}_{u}"
            if v not in self.adj or u not in self.adj[v]:
                edge_data_rev = {
                    "edge_id": rev_edge_id,
                    "s_node_id": v,
                    "e_node_id": u,
                    "length": length,
                    "base_time": b_time,
                    "base_cost": b_cost,
                    "current_cost": b_cost,
                    "congestion_level": 1,
                    "congestion_factor": 1.0,
                    "risk_factor": 1.0,
                    "name": f"Đoạn {v} -> {u}"
                }
                self.adj[v][u] = edge_data_rev

        # 4. Nạp dữ liệu thực tế từ processed_train.csv
        dynamic_count = 0
        if os.path.exists(train_csv):
            print("[INFO] Dang tich hop du lieu giao thong thuc te tu processed_train.csv...")
            df_train = pd.read_csv(train_csv)
            nearby_periods = get_nearby_periods()
            df_train_filtered = df_train[df_train['period'].isin(nearby_periods)].copy()

            if df_train_filtered.empty or len(df_train_filtered) < 100:
                df_train_filtered = df_train.copy()

            df_train_filtered['cost'] = df_train_filtered.apply(
                lambda r: calc_cost(r['time'], r['congestion_factor'], r['risk_factor']), axis=1
            )
            agg_train = df_train_filtered.groupby(['s_node_id', 'e_node_id']).agg({
                'cost': 'mean',
                'congestion_factor': 'mean',
                'risk_factor': 'mean',
                'actual_velocity': 'mean',
                'time': 'mean'
            }).reset_index()

            for _, row in agg_train.iterrows():
                u = int(row['s_node_id'])
                v = int(row['e_node_id'])
                cost = float(row['cost'])
                cong_factor = float(row['congestion_factor'])
                risk_factor = float(row['risk_factor'])
                cong_lvl = map_congestion_to_level(cong_factor)

                edge_id = f"{u}_{v}"
                if u in self.adj and v in self.adj[u]:
                    edge = self.adj[u][v]
                    edge['current_cost'] = cost
                    edge['congestion_level'] = cong_lvl
                    edge['congestion_factor'] = cong_factor
                    edge['risk_factor'] = risk_factor
                    edge['actual_velocity'] = float(row['actual_velocity'])
                    edge['dynamic_time'] = float(row['time'])
                    if edge_id in self.edges:
                        self.edges[edge_id] = edge
                    dynamic_count += 1

                rev_edge_id = f"{v}_{u}"
                if v in self.adj and u in self.adj[v]:
                    rev_edge = self.adj[v][u]
                    rev_edge['current_cost'] = cost
                    rev_edge['congestion_level'] = cong_lvl
                    rev_edge['congestion_factor'] = cong_factor
                    rev_edge['risk_factor'] = risk_factor
                    if rev_edge_id in self.edges:
                        self.edges[rev_edge_id] = rev_edge

            del df_train
            del df_train_filtered
            del agg_train

        self.dynamic_edges_count = dynamic_count

        # 5. Xây dựng edges_cache
        congested_edges = []
        normal_edges = []
        for edge_id, edge in self.edges.items():
            u = edge["s_node_id"]
            v = edge["e_node_id"]
            u_node = self.road_nodes.get(u)
            v_node = self.road_nodes.get(v)
            if u_node and v_node:
                item = {
                    "edge_id": edge_id,
                    "name": edge["name"],
                    "distance": edge["length"],
                    "congestion_level": edge.get("congestion_level", 1),
                    "congestion_factor": round(edge.get("congestion_factor", 1.0), 2),
                    "current_cost": round(edge.get("current_cost", edge["base_cost"]), 2),
                    "u_lat": u_node["lat"],
                    "u_lng": u_node["lng"],
                    "v_lat": v_node["lat"],
                    "v_lng": v_node["lng"]
                }
                if item["congestion_level"] >= 2:
                    congested_edges.append(item)
                else:
                    normal_edges.append(item)

        self.edges_cache = congested_edges + normal_edges

        # 6. Xây dựng cKDTree CHỈ trên các ROAD NODES
        road_ids = []
        road_coords = []
        for n_id, n_data in self.road_nodes.items():
            road_ids.append(n_id)
            road_coords.append((n_data["lat"], n_data["lng"]))

        self.road_node_ids_array = np.array(road_ids)
        if len(road_coords) > 0:
            coords_rad = np.radians(np.array(road_coords))
            self.kdtree = cKDTree(coords_rad)

        # 7. Lọc Bệnh viện & Ánh xạ sang nút giao thông gần nhất
        hospitals_list = []
        for _, row in df_nodes.iterrows():
            p_name = str(row["poi_name"]) if pd.notna(row["poi_name"]) and str(row["poi_name"]) != "None" else None
            p_label = str(row["poi_label"]) if pd.notna(row["poi_label"]) else "Background"
            lat = float(row["lat"])
            lng = float(row["long"])
            n_id = int(row["_id"])

            is_hospital = (
                (p_label.lower() == "hospital") or
                (p_name and any(kw in p_name.lower() for kw in ["bệnh viện", "benh vien", "hospital", "phòng khám", "trạm y tế", "clinic", "y tế"]))
            )

            if is_hospital and p_name:
                nearest_road_node, dist_m = self.find_nearest_road_node(lat, lng)
                target_node_id = nearest_road_node["id"] if nearest_road_node else n_id

                hospitals_list.append({
                    "node_id": target_node_id,
                    "poi_node_id": n_id,
                    "name": p_name,
                    "type": p_label if p_label != "Background" else "Bệnh viện / Cơ sở Y tế",
                    "lat": lat,
                    "lng": lng
                })

        self.hospitals = hospitals_list

        # Giải phóng triệt để bộ nhớ đệm Pandas DataFrames
        del df_nodes
        del df_edges
        gc.collect()

        self.is_loaded = True
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"[OK] Do thi lien thong toi uu san sang: {len(self.road_nodes):,} nut duong, {len(self.edges):,} doan duong, {self.dynamic_edges_count:,} doan cap nhat traffic, {len(self.hospitals)} benh vien ({elapsed:.1f}ms).")

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
                new_d = d + edge["length"]
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
                tentative_g = g + edge["current_cost"]
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
                total_cost += edge["current_cost"]
                total_dist += edge["length"]

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
        "edges_count": len(graph_mgr.edges),
        "dynamic_edges_count": graph_mgr.dynamic_edges_count
    }

@app.get("/api/nodes")
@app.get("/api/v1/nodes")
async def get_nodes(poi_type: Optional[str] = Query("hospital"), limit: int = Query(500)):
    """Hiển thị danh sách các bệnh viện/trạm y tế trên bản đồ"""
    if not poi_type or poi_type == "hospital":
        return graph_mgr.hospitals[:limit]
    return [
        {
            "node_id": n["id"],
            "name": n["poi_name"] or f"POI #{n['id']}",
            "type": n["poi_label"],
            "lat": n["lat"],
            "lng": n["lng"]
        }
        for n in graph_mgr.nodes.values()
        if n["poi_label"] and poi_type.lower() in n["poi_label"].lower()
    ][:limit]

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
    edge = graph_mgr.edges.get(body.edge_id)
    if not edge:
        raise HTTPException(status_code=404, detail="Edge không tồn tại")

    edge["congestion_level"] = body.congestion_level
    edge["current_cost"] = edge["base_cost"] * (1.0 + 0.5 * (body.congestion_level - 1))

    for item in graph_mgr.edges_cache:
        if item["edge_id"] == body.edge_id:
            item["congestion_level"] = body.congestion_level
            break

    return {
        "status": "updated",
        "edge_id": body.edge_id,
        "congestion_level": body.congestion_level
    }
