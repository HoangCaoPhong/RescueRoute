import sys
import os
import gc
import time
import math
import heapq
from datetime import datetime
from collections import deque
from typing import Dict, List, Optional, Any, Tuple, Literal

import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ==========================================
# 1. Đường dẫn tệp & Dữ liệu
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DASHBOARD_HTML = os.path.join(BASE_DIR, "../frontend/dashboard.html")
DASHBOARD_JS = os.path.join(BASE_DIR, "../frontend/dashboard.js")
DASHBOARD_CSS = os.path.join(BASE_DIR, "../frontend/dashboard.css")
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/processed"))

# ==========================================
from scripts import dataset_2_graph
from backend.app.services.hospital_catalog import deduplicate_hospitals

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
        self.emergency_hospitals = []
        self.hospital_kdtree = None
        self.emergency_hospital_kdtree = None
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
        df_road_subset = df_nodes[df_nodes['_id'].isin(needed_road_nodes)]
        for n_id, lat, lng, poi_name in zip(df_road_subset['_id'], df_road_subset['lat'], df_road_subset['long'], df_road_subset['poi_name']):
            n_id = int(n_id)
            p_name = str(poi_name) if pd.notna(poi_name) and str(poi_name) != "None" else None
            self.road_nodes[n_id] = {
                "id": n_id, "lat": float(lat), "lng": float(lng), "poi_name": p_name
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
            
        # Phân loại chuyên sâu các POI Y tế / Bệnh viện cấp cứu
        EXCLUDE_SPEC = [
            "thú y", "thu y", "pet", "dog", "cat", "thú cưng",
            "mắt", "mat", "răng hàm mặt", "rang ham mat", "nha khoa", "da liễu", "da lieu",
            "tâm thần", "tam than", "thẩm mỹ", "tham my", "y học cổ truyền", "phục hồi chức năng", "dưỡng lão"
        ]

        EMERGENCY_KW = [
            "đa khoa", "da khoa", "cấp cứu", "cap cuu", "115", "chợ rẫy", "cho ray",
            "quân y", "quan y", "175", "nhi đồng", "nhi dong", "gia định", "gia dinh",
            "thống nhất", "thong nhat", "trưng vương", "trung vuong", "từ dũ", "tu du",
            "hùng vương", "hung vuong", "nguyễn tri phương", "nguyen tri phuong",
            "quận", "quan", "huyện", "huyen", "thành phố", "thanh pho", "triều an", "trieu an",
            "hoàn mỹ", "hoan my", "pháp việt", "vạn hạnh", "an bình", "xuyên á", "nam sài gòn",
            "tân hưng", "bình dân", "quốc tế"
        ]

        df_poi_subset = df_nodes[df_nodes['poi_name'].notna() | (df_nodes['poi_label'].fillna('').str.lower() != 'background')]
        hospitals_list = []
        pois_list = []

        for n_id, lat, lng, p_name, p_label, poi_distance_m in zip(
            df_poi_subset['_id'],
            df_poi_subset['lat'],
            df_poi_subset['long'],
            df_poi_subset['poi_name'],
            df_poi_subset['poi_label'],
            df_poi_subset['distance_meters'],
        ):
            p_name = str(p_name) if pd.notna(p_name) and str(p_name) != "None" else None
            p_label = str(p_label) if pd.notna(p_label) else "Background"
            lat = float(lat)
            lng = float(lng)
            n_id = int(n_id)

            if not p_name:
                continue

            name_lower = p_name.lower()
            if any(k in name_lower for k in ["thú y", "thu y", "pet", "dog", "cat", "thú cưng"]):
                continue # Bỏ qua thú y

            is_hospital = ((p_label.lower() == "hospital") or any(kw in name_lower for kw in ["bệnh viện", "benh vien", "hospital", "phòng khám", "trạm y tế", "clinic", "y tế"]))
            if is_hospital:
                nearest_road_node, dist_m = self.find_nearest_road_node(lat, lng)
                target_node_id = nearest_road_node["id"] if nearest_road_node else n_id

                is_spec = any(k in name_lower for k in EXCLUDE_SPEC)
                is_emerg_match = any(k in name_lower for k in EMERGENCY_KW)
                is_emergency = (is_emerg_match or ("bệnh viện" in name_lower or "benh vien" in name_lower)) and not is_spec

                item = {
                    "node_id": target_node_id,
                    "poi_node_id": n_id,
                    "name": p_name,
                    "type": p_label if p_label != "Background" else ("Bệnh viện Cấp cứu / Đa khoa" if is_emergency else "Cơ sở Y tế / Phòng khám"),
                    "lat": lat,
                    "lng": lng,
                    "is_hospital": True,
                    "is_emergency": is_emergency,
                    "category": "Cấp cứu / Đa khoa" if is_emergency else "Cơ sở Y tế / Chuyên khoa",
                    "source_distance_m": float(poi_distance_m) if pd.notna(poi_distance_m) else float("inf"),
                }
                hospitals_list.append(item)
            else:
                pois_list.append({
                    "node_id": n_id,
                    "poi_node_id": n_id,
                    "name": p_name,
                    "type": p_label,
                    "lat": lat,
                    "lng": lng,
                    "is_hospital": False,
                    "is_emergency": False
                })

        self.hospitals = deduplicate_hospitals(hospitals_list)
        self.emergency_hospitals = [
            hospital for hospital in self.hospitals if hospital["is_emergency"]
        ]
        self.pois = pois_list
        self.nodes = self.road_nodes # Alias cho tương thích

        # KDTree cho tất cả cơ sở y tế
        h_coords = [(h["lat"], h["lng"]) for h in self.hospitals]
        if len(h_coords) > 0:
            h_coords_rad = np.radians(np.array(h_coords))
            self.hospital_kdtree = cKDTree(h_coords_rad)

        # KDTree cho các bệnh viện cấp cứu / đa khoa tuyến đầu
        eh_coords = [(h["lat"], h["lng"]) for h in self.emergency_hospitals]
        if len(eh_coords) > 0:
            eh_coords_rad = np.radians(np.array(eh_coords))
            self.emergency_hospital_kdtree = cKDTree(eh_coords_rad)

        self.is_loaded = True
        
    def find_nearest_road_node(self, lat: float, lng: float) -> Tuple[Optional[Dict[str, Any]], float]:
        if self.kdtree is None or len(self.road_node_ids_array) == 0:
            return None, 0.0
        query_pt = np.radians([lat, lng])
        dist_rad, idx = self.kdtree.query(query_pt)
        dist_m = float(dist_rad * 6371000.0)
        nearest_id = int(self.road_node_ids_array[idx])
        return self.road_nodes.get(nearest_id), round(dist_m, 1)

    def find_nearest_hospital(self, lat: float, lng: float, emergency_only: bool = True) -> Tuple[Optional[Dict[str, Any]], float]:
        target_list = self.emergency_hospitals if (emergency_only and len(self.emergency_hospitals) > 0) else self.hospitals
        target_tree = self.emergency_hospital_kdtree if (emergency_only and self.emergency_hospital_kdtree is not None) else self.hospital_kdtree

        if not target_list:
            return None, 0.0
        if target_tree is not None and len(target_list) > 0:
            query_pt = np.radians([lat, lng])
            dist_rad, idx = target_tree.query(query_pt)
            dist_m = float(dist_rad * 6371000.0)
            return target_list[idx], round(dist_m, 1)
        
        # Fallback tra cứu bằng khoảng cách Haversine
        best_h = None
        min_dist = float('inf')
        for h in target_list:
            d = haversine(lat, lng, h["lat"], h["lng"])
            if d < min_dist:
                min_dist = d
                best_h = h
        return best_h, round(min_dist, 1)

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

class NearestHospitalRequest(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None

class NearestHospitalRouteRequest(BaseModel):
    start_node_id: Optional[int] = None
    algorithm: str = "astar"
    emergency_only: bool = True

class RouteRequest(BaseModel):
    start_node_id: Optional[int] = None
    goal_node_id: int
    algorithm: str = "astar"

class MultiLocationRouteRequest(BaseModel):
    start_node_id: Optional[int] = None
    waypoint_ids: List[int] = Field(default_factory=list, max_length=10)
    goal_node_id: int
    route_algorithm: Literal[
        "bfs", "dfs", "ucs", "astar", "dijkstra", "hill_climbing"
    ] = "astar"
    optimization_method: Literal["nearest_neighbor", "held_karp", "genetic_algorithm", "simulated_annealing"] = (
        "nearest_neighbor"
    )
    criterion: Literal["cost", "distance", "hops", "time"] = "cost"

class MultiLocationRouteResponse(BaseModel):
    found: bool
    message: Optional[str] = None
    route_algorithm: Optional[str] = None
    optimization_method: Optional[str] = None
    criterion: Optional[str] = None
    order_is_optimal: Optional[bool] = None
    is_optimal: Optional[bool] = None
    visiting_order: List[int] = Field(default_factory=list)
    ordered_waypoints: List[int] = Field(default_factory=list)
    objective_cost: Optional[float] = None
    original_order: List[int] = Field(default_factory=list)
    original_objective_cost: Optional[float] = None
    segments: List[Dict[str, Any]] = Field(default_factory=list)
    path_nodes: List[int] = Field(default_factory=list)
    path_coords: List[List[float]] = Field(default_factory=list)
    total_cost: Optional[float] = None
    total_distance_m: Optional[float] = None
    nodes_expanded: Optional[int] = None
    execution_time_ms: Optional[float] = None

class CongestionRequest(BaseModel):
    edge_id: str
    congestion_level: int

# ==========================================
# 5. Thuật toán Tìm đường trên Đồ thị
# ==========================================
from backend.app.services.routing_service import (
    haversine,
    run_multi_location_search,
    run_search,
    run_search_nearest_hospital,
)

# ==========================================
# 6. Các API Endpoints
# ==========================================
@app.get("/")
@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard():
    """Mở trực tiếp giao diện Dashboard bản đồ"""
    if os.path.exists(DASHBOARD_HTML):
        return FileResponse(DASHBOARD_HTML)
    return {"message": "dashboard.html không tìm thấy"}

@app.get("/dashboard.js", response_class=FileResponse)
async def serve_dashboard_js():
    """Serve the dashboard javascript file"""
    if os.path.exists(DASHBOARD_JS):
        return FileResponse(DASHBOARD_JS)
    return {"message": "dashboard.js không tìm thấy"}

@app.get("/dashboard.css", response_class=FileResponse)
async def serve_dashboard_css():
    """Serve the dashboard css file"""
    if os.path.exists(DASHBOARD_CSS):
        return FileResponse(DASHBOARD_CSS)
    return {"message": "dashboard.css không tìm thấy"}

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
async def get_nodes(
    poi_type: Optional[str] = Query("hospital"),
    emergency_only: Optional[bool] = Query(False),
    limit: int = Query(570000)
):
    """Hiển thị danh sách các bệnh viện/trạm y tế và POI trên bản đồ"""
    if not poi_type or poi_type == "hospital":
        if emergency_only:
            return graph_mgr.emergency_hospitals[:limit]
        return graph_mgr.hospitals[:limit]
    if poi_type == "emergency":
        return graph_mgr.emergency_hospitals[:limit]
    if poi_type == "all":
        return (graph_mgr.hospitals + graph_mgr.pois)[:limit]
    return [p for p in graph_mgr.pois if p["type"] and poi_type.lower() in p["type"].lower()][:limit]

@app.get("/api/hospitals/nearest")
@app.get("/api/v1/hospitals/nearest")
async def get_nearest_hospital(
    lat: Optional[float] = Query(None, description="Vĩ độ vị trí truy vấn (mặc định lấy theo vị trí xe cấp cứu)"),
    lng: Optional[float] = Query(None, description="Kinh độ vị trí truy vấn (mặc định lấy theo vị trí xe cấp cứu)"),
    emergency_only: bool = Query(True, description="Chỉ tìm các bệnh viện có khoa cấp cứu / đa khoa")
):
    """Tìm bệnh viện / cơ sở y tế gần nhất theo tọa độ GPS bằng KD-Tree"""
    query_lat = lat if lat is not None else graph_mgr.ambulance_lat
    query_lng = lng if lng is not None else graph_mgr.ambulance_lng

    nearest_hospital, dist_m = graph_mgr.find_nearest_hospital(query_lat, query_lng, emergency_only=emergency_only)
    if not nearest_hospital:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh viện phù hợp trong hệ thống")

    return {
        "status": "success",
        "query_location": {
            "lat": query_lat,
            "lng": query_lng
        },
        "emergency_only": emergency_only,
        "nearest_hospital": nearest_hospital,
        "distance_meters": dist_m,
        "distance_km": round(dist_m / 1000.0, 2)
    }

@app.post("/api/hospitals/nearest")
@app.post("/api/v1/hospitals/nearest")
async def post_nearest_hospital(body: Optional[NearestHospitalRequest] = None):
    """Tìm bệnh viện / cơ sở y tế gần nhất qua POST request"""
    query_lat = body.lat if (body and body.lat is not None) else graph_mgr.ambulance_lat
    query_lng = body.lng if (body and body.lng is not None) else graph_mgr.ambulance_lng

    nearest_hospital, dist_m = graph_mgr.find_nearest_hospital(query_lat, query_lng, emergency_only=True)
    if not nearest_hospital:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh viện phù hợp trong hệ thống")

    return {
        "status": "success",
        "query_location": {
            "lat": query_lat,
            "lng": query_lng
        },
        "emergency_only": True,
        "nearest_hospital": nearest_hospital,
        "distance_meters": dist_m,
        "distance_km": round(dist_m / 1000.0, 2)
    }

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
    """Run A*, Dijkstra, BFS, DFS, UCS, or Hill Climbing and draw the route."""
    start_id = body.start_node_id
    if start_id is None:
        nearest_node, _ = graph_mgr.find_nearest_road_node(graph_mgr.ambulance_lat, graph_mgr.ambulance_lng)
        start_id = nearest_node["id"] if nearest_node else list(graph_mgr.road_nodes.keys())[0]

    # Nếu goal_node_id <= 0 -> Chế độ tự động dò tìm BV gần nhất trên đồ thị (Multi-Goal Search)
    if body.goal_node_id is None or body.goal_node_id <= 0:
        return run_search_nearest_hospital(graph_mgr, start_id, body.algorithm, emergency_only=True)

    return run_search(graph_mgr, start_id, body.goal_node_id, body.algorithm)

@app.post("/api/route/multi-location", response_model=MultiLocationRouteResponse)
@app.post("/api/v1/route/multi-location", response_model=MultiLocationRouteResponse)
async def calculate_multi_location_route(body: MultiLocationRouteRequest):
    """Optimize waypoint order with Nearest Neighbor or Held-Karp."""

    start_id = body.start_node_id
    if start_id is None:
        nearest_node, _ = graph_mgr.find_nearest_road_node(
            graph_mgr.ambulance_lat,
            graph_mgr.ambulance_lng,
        )
        start_id = (
            nearest_node["id"]
            if nearest_node
            else list(graph_mgr.road_nodes.keys())[0]
        )
    return run_multi_location_search(
        graph_mgr,
        start_id,
        body.waypoint_ids,
        body.goal_node_id,
        body.route_algorithm,
        body.optimization_method,
        body.criterion,
    )

@app.post("/api/route/nearest-hospital")
@app.post("/api/v1/route/nearest-hospital")
async def calculate_nearest_hospital_route(body: NearestHospitalRouteRequest):
    """Tự động dùng thuật toán AI dò đường trên mạng lưới đồ thị để tìm bệnh viện cấp cứu tối ưu nhất mà không cần biết trước điểm đích"""
    start_id = body.start_node_id
    if start_id is None:
        nearest_node, _ = graph_mgr.find_nearest_road_node(graph_mgr.ambulance_lat, graph_mgr.ambulance_lng)
        start_id = nearest_node["id"] if nearest_node else list(graph_mgr.road_nodes.keys())[0]

    return run_search_nearest_hospital(graph_mgr, start_id, body.algorithm, emergency_only=body.emergency_only)

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
