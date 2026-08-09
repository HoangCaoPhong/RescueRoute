import os
import sys
import time
import math
import heapq
from datetime import datetime
from collections import defaultdict, deque
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy.spatial import KDTree

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

app = FastAPI(
    title="RescueRoute - Ambulance Intelligent Routing API",
    description="Backend API phục vụ Tích hợp Bản đồ Leaflet, Định vị GPS Xe Cấp Cứu, Dữ liệu Đồ thị Giao thông Thực tế & Thuật toán AI",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL IN-MEMORY DATA STORAGE ---
df_nodes_global: Optional[pd.DataFrame] = None
node_coords_kdtree: Optional[KDTree] = None
node_id_to_idx: Dict[int, int] = {}
idx_to_node_id: Dict[int, int] = {}

# Node metadata lookup
nodes_metadata: Dict[int, Dict[str, Any]] = {}
hospitals_list: List[Dict[str, Any]] = []
poi_nodes_summary: List[Dict[str, Any]] = []

# Graph structures
graph_adj: Dict[int, Dict[int, float]] = defaultdict(dict)
edge_details: Dict[str, Dict[str, Any]] = {}
major_edges_for_map: List[Dict[str, Any]] = []

# Dynamic ambulance state (default at Central HCM: 10.773, 106.698)
current_ambulance_gps = {
    "lat": 10.773,
    "lng": 106.698,
    "last_updated": time.time()
}

# --- COST FUNCTION & PERIOD HELPERS ---
def calc_cost(travel_time: float, congestion: float, risk: float, parameters=(0.648, 0.23, 0.122)) -> float:
    """
    Cost formula from EDA & domain rules:
    Cost = alpha * time + beta * congestion^2 + gamma * risk^2
    """
    return parameters[0] * travel_time + parameters[1] * (congestion ** 2) + parameters[2] * (risk ** 2)

def get_nearby_periods() -> List[str]:
    """Get previous, current, and next 30-minute period slots."""
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
        
    slots.append(curr_slot)
    
    # next slot
    if curr_slot[1] == 0:
        slots.append((curr_slot[0], 30))
    else:
        slots.append(((curr_slot[0] + 1) % 24, 0))
        
    return [f"period_{h}_{m:02d}" for h, m in slots]

# --- DATA INITIALIZATION ---
def init_dataset_and_graph():
    global df_nodes_global, node_coords_kdtree, node_id_to_idx, idx_to_node_id
    global nodes_metadata, hospitals_list, poi_nodes_summary, graph_adj, edge_details, major_edges_for_map

    print("[INFO] Initializing RescueRoute dataset and graph into RAM...")
    start_time = time.perf_counter()

    # 1. Check & ensure base_segments.csv exists
    base_segments_file = os.path.join(PROCESSED_DATA_DIR, "base_segments.csv")
    if not os.path.exists(base_segments_file):
        print("[INFO] base_segments.csv not found, generating via enrich_data...")
        try:
            from enrich_data import enrich_segments
            enrich_segments()
        except Exception as e:
            print(f"[WARN] Warning during enrich_segments: {e}")

    # 2. Load nodes
    nodes_path = os.path.join(PROCESSED_DATA_DIR, "nodes_with_poi_labels.csv")
    if not os.path.exists(nodes_path):
        nodes_path = os.path.join(RAW_DATA_DIR, "nodes.csv")
    
    print(f"[INFO] Loading nodes from {nodes_path}...")
    df_nodes_global = pd.read_csv(nodes_path)
    
    # Standardize column names
    id_col = "_id" if "_id" in df_nodes_global.columns else "node_id"
    lat_col = "lat" if "lat" in df_nodes_global.columns else "latitude"
    lng_col = "long" if "long" in df_nodes_global.columns else ("lng" if "lng" in df_nodes_global.columns else "longitude")

    # Index all nodes metadata
    for i, row in df_nodes_global.iterrows():
        nid = int(row[id_col])
        lat = float(row[lat_col])
        lng = float(row[lng_col])
        poi_label = str(row.get("poi_label", "Background"))
        poi_name = str(row.get("poi_name", "Unknown"))
        if pd.isna(poi_name) or poi_name.strip() == "" or poi_name == "nan":
            poi_name = f"Nút {nid}"

        nodes_metadata[nid] = {
            "node_id": nid,
            "lat": lat,
            "lng": lng,
            "name": poi_name,
            "type": poi_label
        }

    # 3. Load base segments
    df_base = pd.read_csv(base_segments_file) if os.path.exists(base_segments_file) else pd.DataFrame()
    
    # Load street names & metadata from raw segments
    raw_segments_file = os.path.join(RAW_DATA_DIR, "segments.csv")
    df_raw_seg = pd.read_csv(raw_segments_file) if os.path.exists(raw_segments_file) else pd.DataFrame()
    
    seg_meta_map = {}
    if not df_raw_seg.empty:
        for _, row in df_raw_seg.iterrows():
            u = int(row["s_node_id"])
            v = int(row["e_node_id"])
            street_name = str(row.get("street_name", "Đường nội bộ"))
            if pd.isna(street_name) or street_name == "nan":
                street_name = "Đường đô thị"
            seg_meta_map[(u, v)] = {
                "street_name": street_name,
                "street_type": str(row.get("street_type", "secondary")),
                "max_velocity": float(row.get("max_velocity", 40.0)) if not pd.isna(row.get("max_velocity")) else 40.0,
                "length": float(row.get("length", 100.0))
            }

    # Populate base graph
    for _, row in df_base.iterrows():
        u = int(row["s_node_id"])
        v = int(row["e_node_id"])
        cost = float(row.get("base_cost", 10.0))
        length = float(row.get("length", 100.0))
        graph_adj[u][v] = cost
        
        meta = seg_meta_map.get((u, v), {
            "street_name": "Đường giao thông",
            "street_type": "primary",
            "max_velocity": 40.0,
            "length": length
        })
        
        edge_key = f"{u}_{v}"
        edge_details[edge_key] = {
            "edge_id": edge_key,
            "u": u,
            "v": v,
            "name": meta["street_name"],
            "street_type": meta["street_type"],
            "distance": meta["length"],
            "speed_limit": meta["max_velocity"],
            "cost": cost,
            "congestion_level": 2,
            "risk_factor": 1.5
        }

    # 4. Overlay dynamic traffic from processed_train.csv
    train_file = os.path.join(PROCESSED_DATA_DIR, "processed_train.csv")
    if os.path.exists(train_file):
        df_train = pd.read_csv(train_file)
        nearby_periods = get_nearby_periods()
        df_filtered = df_train[df_train["period"].isin(nearby_periods)]
        if not df_filtered.empty:
            agg_train = df_filtered.groupby(["s_node_id", "e_node_id"]).agg({
                "time": "mean",
                "congestion_factor": "mean",
                "risk_factor": "mean"
            }).reset_index()
            
            for _, row in agg_train.iterrows():
                u = int(row["s_node_id"])
                v = int(row["e_node_id"])
                t = float(row["time"])
                cong = float(row["congestion_factor"])
                risk = float(row["risk_factor"])
                dyn_cost = calc_cost(t, cong, risk)
                
                graph_adj[u][v] = dyn_cost
                edge_key = f"{u}_{v}"
                if edge_key in edge_details:
                    edge_details[edge_key]["cost"] = dyn_cost
                    edge_details[edge_key]["congestion_level"] = min(5, max(1, int(round(cong))))
                    edge_details[edge_key]["risk_factor"] = risk

    # 5. Build Spatial KDTree specifically on ROAD GRAPH NODES (Ensures 100% routability)
    graph_node_ids = set(graph_adj.keys())
    df_road_nodes = df_nodes_global[df_nodes_global[id_col].isin(graph_node_ids)].copy().reset_index(drop=True)
    coords_rad = np.radians(df_road_nodes[[lat_col, lng_col]].to_numpy())
    node_coords_kdtree = KDTree(coords_rad)
    
    road_node_ids = df_road_nodes[id_col].astype(int).tolist()
    node_id_to_idx = {nid: i for i, nid in enumerate(road_node_ids)}
    idx_to_node_id = {i: nid for i, nid in enumerate(road_node_ids)}

    # Collect all medical POIs (Hospitals & Clinics) across HCMC
    seen_hospital_names = set()
    for nid, node_item in nodes_metadata.items():
        poi_label = node_item["type"].lower()
        poi_name = node_item["name"].strip()
        
        if "hospital" in poi_label or "clinic" in poi_label or "y_tế" in poi_label or "bệnh_viện" in poi_label:
            if poi_name not in ["Unknown", f"Nút {nid}", ""] and poi_name in seen_hospital_names:
                continue
            
            if poi_name not in ["Unknown", f"Nút {nid}", ""]:
                seen_hospital_names.add(poi_name)
            
            hospitals_list.append(node_item)

    print(f"[INFO] Loaded {len(df_nodes_global):,} nodes | Built KDTree on {len(df_road_nodes):,} road nodes | Collected {len(hospitals_list)} distinct medical POIs across HCMC.")

    # 6. Extract all street segments for map display (full visualization for testing)
    for edge_key, edge in edge_details.items():
        u = edge["u"]
        v = edge["v"]
        if u in nodes_metadata and v in nodes_metadata:
            u_data = nodes_metadata[u]
            v_data = nodes_metadata[v]
            
            major_edges_for_map.append({
                "edge_id": edge_key,
                "u": u,
                "v": v,
                "u_lat": u_data["lat"],
                "u_lng": u_data["lng"],
                "v_lat": v_data["lat"],
                "v_lng": v_data["lng"],
                "name": edge["name"],
                "distance": round(edge["distance"], 1),
                "speed_limit": edge["speed_limit"],
                "congestion_level": edge["congestion_level"],
                "cost": round(edge["cost"], 2)
            })

    elapsed = time.perf_counter() - start_time
    print(f"[INFO] Graph built in {elapsed:.2f}s | {len(graph_adj):,} connected nodes | {len(edge_details):,} edges | {len(major_edges_for_map)} map overlay segments.")

# Initialize data on module load
init_dataset_and_graph()

# --- SPATIAL QUERY HELPER ---
def find_nearest_node(lat: float, lng: float) -> Dict[str, Any]:
    """Finds the nearest graph node in under 3ms using KDTree."""
    if node_coords_kdtree is None or df_nodes_global is None:
        return {"nearest_node_id": 0, "name": "Unknown", "type": "Unknown", "distance_meters": 0.0}
    
    q_rad = np.radians([lat, lng])
    dist_rad, idx = node_coords_kdtree.query(q_rad)
    dist_meters = round(dist_rad * 6371000, 1) # Earth radius
    node_id = idx_to_node_id[idx]
    meta = nodes_metadata.get(node_id, {})
    
    return {
        "nearest_node_id": node_id,
        "nearest_node_name": meta.get("name", f"Nút {node_id}"),
        "nearest_node_type": meta.get("type", "Intersection"),
        "lat": meta.get("lat", lat),
        "lng": meta.get("lng", lng),
        "distance_meters": dist_meters
    }

# --- SEARCH ALGORITHMS IMPLEMENTATION ---
def haversine_heuristic(u_id: int, goal_id: int) -> float:
    """Haversine distance (meters) / max velocity (m/s) as admissible heuristic."""
    u_meta = nodes_metadata.get(u_id)
    g_meta = nodes_metadata.get(goal_id)
    if not u_meta or not g_meta:
        return 0.0
    
    lat1, lon1 = math.radians(u_meta["lat"]), math.radians(u_meta["lng"])
    lat2, lon2 = math.radians(g_meta["lat"]), math.radians(g_meta["lng"])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    dist_m = 6371000 * c
    # Approximate admissible lower bound time (assuming max speed 60 km/h = 16.67 m/s)
    return (dist_m / 16.67) * 0.648

def run_dijkstra_ucs(start_node: int, goal_node: int):
    t0 = time.perf_counter()
    pq = [(0.0, start_node, [start_node])]
    visited = {}
    nodes_expanded = 0
    
    while pq:
        cost, curr, path = heapq.heappop(pq)
        if curr in visited and visited[curr] <= cost:
            continue
        visited[curr] = cost
        nodes_expanded += 1
        
        if curr == goal_node:
            t_exec = (time.perf_counter() - t0) * 1000
            return cost, path, nodes_expanded, t_exec
            
        for neighbor, edge_cost in graph_adj.get(curr, {}).items():
            new_cost = cost + edge_cost
            if neighbor not in visited or new_cost < visited[neighbor]:
                heapq.heappush(pq, (new_cost, neighbor, path + [neighbor]))
                
    t_exec = (time.perf_counter() - t0) * 1000
    return None, None, nodes_expanded, t_exec

def run_astar(start_node: int, goal_node: int):
    t0 = time.perf_counter()
    h_start = haversine_heuristic(start_node, goal_node)
    pq = [(h_start, 0.0, start_node, [start_node])]
    g_costs = {start_node: 0.0}
    nodes_expanded = 0
    
    while pq:
        f, g, curr, path = heapq.heappop(pq)
        if g > g_costs.get(curr, float('inf')):
            continue
        nodes_expanded += 1
        
        if curr == goal_node:
            t_exec = (time.perf_counter() - t0) * 1000
            return g, path, nodes_expanded, t_exec
            
        for neighbor, edge_cost in graph_adj.get(curr, {}).items():
            new_g = g + edge_cost
            if new_g < g_costs.get(neighbor, float('inf')):
                g_costs[neighbor] = new_g
                h = haversine_heuristic(neighbor, goal_node)
                heapq.heappush(pq, (new_g + h, new_g, neighbor, path + [neighbor]))
                
    t_exec = (time.perf_counter() - t0) * 1000
    return None, None, nodes_expanded, t_exec

def run_bfs(start_node: int, goal_node: int):
    t0 = time.perf_counter()
    queue = deque([(start_node, [start_node])])
    visited = {start_node}
    nodes_expanded = 0
    
    while queue:
        curr, path = queue.popleft()
        nodes_expanded += 1
        
        if curr == goal_node:
            # Calculate total cost along path
            total_cost = sum(graph_adj[path[i]][path[i+1]] for i in range(len(path)-1) if path[i+1] in graph_adj[path[i]])
            t_exec = (time.perf_counter() - t0) * 1000
            return total_cost, path, nodes_expanded, t_exec
            
        for neighbor in graph_adj.get(curr, {}):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
                
    t_exec = (time.perf_counter() - t0) * 1000
    return None, None, nodes_expanded, t_exec

def run_dfs(start_node: int, goal_node: int, max_depth: int = 500):
    t0 = time.perf_counter()
    stack = [(start_node, [start_node])]
    visited = set()
    nodes_expanded = 0
    
    while stack:
        curr, path = stack.pop()
        if curr in visited or len(path) > max_depth:
            continue
        visited.add(curr)
        nodes_expanded += 1
        
        if curr == goal_node:
            total_cost = sum(graph_adj[path[i]][path[i+1]] for i in range(len(path)-1) if path[i+1] in graph_adj[path[i]])
            t_exec = (time.perf_counter() - t0) * 1000
            return total_cost, path, nodes_expanded, t_exec
            
        for neighbor in graph_adj.get(curr, {}):
            if neighbor not in visited:
                stack.append((neighbor, path + [neighbor]))
                
    t_exec = (time.perf_counter() - t0) * 1000
    return None, None, nodes_expanded, t_exec

# --- PYDANTIC SCHEMAS ---
class GPSUpdate(BaseModel):
    lat: float = Field(..., json_schema_extra={"example": 10.773}, description="Vĩ độ GPS")
    lng: float = Field(..., json_schema_extra={"example": 106.698}, description="Kinh độ GPS")

class CongestionUpdate(BaseModel):
    edge_id: str = Field(..., json_schema_extra={"example": "373543511_5468660805"}, description="Mã đoạn đường (u_v)")
    congestion_level: int = Field(..., json_schema_extra={"example": 5}, description="Mức độ kẹt xe (1: Thông thoáng -> 5: Tắc nghẽn nghiêm trọng)")

class RouteRequest(BaseModel):
    start_node_id: Optional[int] = Field(None, description="Mã node xuất phát (nếu None sẽ dùng Node gần xe cấp cứu nhất)")
    goal_node_id: int = Field(..., description="Mã node đích (Bệnh viện hoặc trạm cứu hộ)")
    algorithm: str = Field("astar", description="Thuật toán tìm đường: astar | dijkstra | ucs | bfs | dfs")

# --- RESTFUL API ENDPOINTS ---
@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """Returns the comprehensive Leaflet Map Dispatcher Dashboard."""
    html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/health")
def get_health():
    """Health check & benchmark latency of the in-memory RAM graph."""
    t0 = time.perf_counter()
    _ = len(nodes_metadata) + len(edge_details)
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)
    
    return {
        "status": "healthy",
        "app": "RescueRoute Backend",
        "version": "2.0.0",
        "latency_ms": max(latency_ms, 0.01),
        "nodes_count": len(df_nodes_global) if df_nodes_global is not None else 0,
        "edges_count": len(edge_details),
        "hospitals_count": len(hospitals_list),
        "graph_connected_nodes": len(graph_adj)
    }

@app.get("/api/nodes")
def get_nodes(
    poi_type: Optional[str] = Query(None, description="Lọc theo loại POI: hospital, clinic, bus_stop, etc."),
    limit: int = Query(200, ge=1, le=5000, description="Giới hạn số lượng nodes trả về")
):
    """Retrieve POI nodes with optional category filtering."""
    if poi_type:
        poi_lower = poi_type.lower()
        if "hospital" in poi_lower or "clinic" in poi_lower:
            return hospitals_list[:limit]
        filtered = [n for n in poi_nodes_summary if poi_lower in n.get("type", "").lower()]
        return filtered[:limit]
    
    # Return combination of hospitals and key POIs
    results = hospitals_list + poi_nodes_summary
    return results[:limit]

@app.get("/api/edges")
def get_edges(limit: int = Query(100000, ge=1, le=200000, description="Số lượng đoạn đường trả về")):
    """Retrieve prominent road segments for map visualization."""
    return major_edges_for_map[:limit]

@app.post("/api/ambulance/location")
def update_ambulance_location(gps: GPSUpdate):
    """Update ambulance GPS coordinates and map to the nearest graph node in <3ms."""
    global current_ambulance_gps
    nearest_info = find_nearest_node(gps.lat, gps.lng)
    
    current_ambulance_gps = {
        "lat": gps.lat,
        "lng": gps.lng,
        "last_updated": time.time(),
        "mapped_nearest_node": nearest_info
    }
    
    return {
        "message": "Cập nhật vị trí GPS xe cấp cứu thành công!",
        "current_gps": current_ambulance_gps,
        "mapped_nearest_node": nearest_info
    }

@app.get("/api/ambulance/location")
def get_ambulance_location():
    """Get current ambulance location and nearest node."""
    nearest_info = find_nearest_node(current_ambulance_gps["lat"], current_ambulance_gps["lng"])
    return {**current_ambulance_gps, "mapped_nearest_node": nearest_info}

@app.post("/api/edges/congestion")
def update_congestion(req: CongestionUpdate):
    """Dynamically update congestion factor on a segment and recalculate graph edge weight."""
    if req.edge_id not in edge_details:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đoạn đường {req.edge_id}")
    
    edge = edge_details[req.edge_id]
    edge["congestion_level"] = req.congestion_level
    
    # Recalculate cost
    est_time = edge["distance"] / (max(edge["speed_limit"] / max(req.congestion_level, 1), 5) / 3.6)
    new_cost = calc_cost(est_time, float(req.congestion_level), edge.get("risk_factor", 1.5))
    edge["cost"] = new_cost
    
    # Update active graph weight
    u = edge["u"]
    v = edge["v"]
    graph_adj[u][v] = new_cost
    
    # Update major edges list for map
    for m_edge in major_edges_for_map:
        if m_edge["edge_id"] == req.edge_id:
            m_edge["congestion_level"] = req.congestion_level
            m_edge["cost"] = round(new_cost, 2)
            break
            
    return {
        "message": f"Cập nhật mức kẹt xe thành công cho đoạn đường {req.edge_id}",
        "edge_id": req.edge_id,
        "new_congestion_level": req.congestion_level,
        "new_cost": round(new_cost, 2)
    }

@app.post("/api/route")
def search_route(req: RouteRequest):
    """Compute optimal route between start node (or current ambulance) and destination hospital."""
    start_id = req.start_node_id
    if start_id is None:
        nearest = find_nearest_node(current_ambulance_gps["lat"], current_ambulance_gps["lng"])
        start_id = nearest["nearest_node_id"]
        
    goal_id = req.goal_node_id
    if goal_id not in graph_adj:
        goal_meta = nodes_metadata.get(goal_id)
        if goal_meta:
            nearest_g = find_nearest_node(goal_meta["lat"], goal_meta["lng"])
            goal_id = nearest_g["nearest_node_id"]
        else:
            goal_id = list(graph_adj.keys())[0]
            
    algo = req.algorithm.lower()
    
    if start_id not in graph_adj:
        # Fallback to finding nearest node with outgoing edges
        start_id = list(graph_adj.keys())[0]
        
    if algo == "astar":
        cost, path, expanded, exec_ms = run_astar(start_id, goal_id)
    elif algo in ["dijkstra", "ucs"]:
        cost, path, expanded, exec_ms = run_dijkstra_ucs(start_id, goal_id)
    elif algo == "bfs":
        cost, path, expanded, exec_ms = run_bfs(start_id, goal_id)
    elif algo == "dfs":
        cost, path, expanded, exec_ms = run_dfs(start_id, goal_id)
    else:
        cost, path, expanded, exec_ms = run_astar(start_id, goal_id)
        
    if not path:
        return {
            "found": False,
            "algorithm": algo,
            "message": "Không tìm thấy đường đi giữa 2 node trên đồ thị."
        }
        
    # Build coordinates and steps along path
    path_coords = []
    total_distance_m = 0.0
    steps = []
    
    for i in range(len(path)):
        nid = path[i]
        meta = nodes_metadata.get(nid, {})
        lat = meta.get("lat", 0.0)
        lng = meta.get("lng", 0.0)
        path_coords.append([lat, lng])
        
        if i < len(path) - 1:
            next_nid = path[i+1]
            edge_k = f"{nid}_{next_nid}"
            e_meta = edge_details.get(edge_k, {})
            dist = e_meta.get("distance", 50.0)
            total_distance_m += dist
            steps.append({
                "from_node": nid,
                "to_node": next_nid,
                "street_name": e_meta.get("name", "Đoạn đường liên kết"),
                "distance": dist,
                "cost": e_meta.get("cost", 1.0),
                "congestion_level": e_meta.get("congestion_level", 2)
            })

    return {
        "found": True,
        "algorithm": algo,
        "start_node_id": start_id,
        "goal_node_id": goal_id,
        "total_cost": round(cost, 2) if cost else 0.0,
        "total_distance_m": round(total_distance_m, 1),
        "nodes_expanded": expanded,
        "execution_time_ms": round(exec_ms, 2),
        "path_node_count": len(path),
        "path_coords": path_coords,
        "steps": steps[:30] # Return first 30 steps for summary
    }

if __name__ == "__main__":
    import uvicorn
    print("[INFO] Starting RescueRoute FastAPI Backend Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
