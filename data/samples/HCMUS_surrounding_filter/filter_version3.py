from pathlib import Path
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

# ============================================================
# CONFIG & CONSTANTS
# ============================================================
INPUT_DIR = Path(".")
OUTPUT_DIR = Path("output")
OUTPUT_IMAGE = OUTPUT_DIR / "graph_clean.png"

HCMUS = {"name": "HCMUS", "lat": 10.7628866, "lon": 106.6825046}
HOSPITALS = {
    "Bệnh viện Từ Dũ": {"lat": 10.76889, "lon": 106.68601},
    "Bệnh viện Nguyễn Tri Phương": {"lat": 10.75537, "lon": 106.66998},
    "Bệnh viện Phạm Ngọc Thạch": {"lat": 10.75722, "lon": 106.66505},
    "Bệnh viện Đại học Y Dược TP.HCM": {"lat": 10.75527, "lon": 106.66457},
    "Bệnh viện Hùng Vương": {"lat": 10.75623, "lon": 106.66166},
    "Bệnh viện Chợ Rẫy": {"lat": 10.75695, "lon": 106.65973},
}

NUMBER_OF_HOSPITALS = 4
POINT_ON_SEGMENT_TOLERANCE = 3.0
ENDPOINT_TOLERANCE = 2.0
FILES = ["nodes.csv", "segments.csv", "streets.csv", "segment_status.csv", "train.csv"]

# ============================================================
# UTILS: MATH & GEOMETRY
# ============================================================
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1)/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1)/2)**2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))

def latlon_to_xy(lat, lon, ref_lat):
    R = 6371000.0
    return R * np.radians(lon) * np.cos(np.radians(ref_lat)), R * np.radians(lat)

def point_to_segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length_sq = dx*dx + dy*dy
    if length_sq == 0: return math.hypot(px - ax, py - ay), 0.0
    t = max(0.0, min(1.0, ((px - ax)*dx + (py - ay)*dy) / length_sq))
    return math.hypot(px - (ax + t*dx), py - (ay + t*dy)), t

# ============================================================
# DATA PIPELINE
# ============================================================
def check_files():
    missing = [f for f in FILES if not (INPUT_DIR / f).exists()]
    if missing: raise FileNotFoundError(f"Thiếu file: {', '.join(missing)}")

def load_data():
    dfs = tuple(pd.read_csv(INPUT_DIR / f) for f in FILES)
    for f, df in zip(FILES, dfs): print(f"{f:18}: {len(df):,}")
    return dfs

def find_nearest_hospitals():
    hosps = sorted([{"name": k, "lat": v["lat"], "lon": v["lon"], 
                     "distance": float(haversine(HCMUS["lat"], HCMUS["lon"], v["lat"], v["lon"]))} 
                    for k, v in HOSPITALS.items()], key=lambda x: x["distance"])[:NUMBER_OF_HOSPITALS]
    for i, h in enumerate(hosps, 1): print(f"{i}. {h['name']} - {h['distance']:.3f} km")
    return hosps, hosps[-1]["distance"]

def filter_segments(nodes, segments, radius):
    lookup = nodes.set_index("_id")[["lat", "long"]]
    seg = segments.dropna(subset=["s_node_id", "e_node_id"]).copy()
    seg["s_lat"], seg["s_long"] = seg["s_node_id"].map(lookup["lat"]), seg["s_node_id"].map(lookup["long"])
    seg["e_lat"], seg["e_long"] = seg["e_node_id"].map(lookup["lat"]), seg["e_node_id"].map(lookup["long"])
    seg = seg.dropna(subset=["s_lat", "s_long", "e_lat", "e_long"])
    
    d_start = haversine(seg["s_lat"], seg["s_long"], HCMUS["lat"], HCMUS["lon"])
    d_end = haversine(seg["e_lat"], seg["e_long"], HCMUS["lat"], HCMUS["lon"])
    filtered = seg[(d_start <= radius) | (d_end <= radius)].drop(
        columns=["s_lat", "s_long", "e_lat", "e_long"], errors="ignore")
    print(f"Segments filter: {len(segments)} -> {len(filtered)}")
    return filtered

def filter_nodes(nodes, segments):
    used = set(segments["s_node_id"].astype(int)) | set(segments["e_node_id"].astype(int))
    return nodes[nodes["_id"].isin(used)].copy()

def find_intermediate_nodes(nodes, segments):
    node_lookup = {int(r["_id"]): {"lat": r["lat"], "lon": r["long"], **dict(zip(["x","y"], latlon_to_xy(r["lat"], r["long"], HCMUS["lat"])))} for _, r in nodes.iterrows()}
    idx = {}
    for _, r in segments.iterrows():
        idx.setdefault(int(r["s_node_id"]), []).append(int(r["_id"]))
        idx.setdefault(int(r["e_node_id"]), []).append(int(r["_id"]))
        
    unique_segs = {tuple(sorted([int(r["s_node_id"]), int(r["e_node_id"])])): r for _, r in segments.iterrows() if r["s_node_id"] != r["e_node_id"]}
    candidates = {}
    
    for (a, b) in unique_segs:
        if a not in node_lookup or b not in node_lookup: continue
        ax, ay, bx, by = node_lookup[a]["x"], node_lookup[a]["y"], node_lookup[b]["x"], node_lookup[b]["y"]
        seg_len = math.hypot(bx - ax, by - ay)
        
        for nid, pt in node_lookup.items():
            if nid in (a, b) or not idx.get(nid): continue
            dist, t = point_to_segment_distance(pt["x"], pt["y"], ax, ay, bx, by)
            if 0.0 < t < 1.0 and dist <= POINT_ON_SEGMENT_TOLERANCE:
                if (seg_len * t) >= ENDPOINT_TOLERANCE and (seg_len * (1.0 - t)) >= ENDPOINT_TOLERANCE:
                    candidates[(nid, min(a, b), max(a, b))] = {"node_id": nid, "a": a, "b": b, "t": t, "distance": dist}
    return list(candidates.values())

def split_segments(nodes, segments):
    cands = find_intermediate_nodes(nodes, segments)
    if not cands: return segments.copy(), {}

    split_map = {}
    for c in cands: split_map.setdefault(tuple(sorted([c["a"], c["b"]])), []).append((c["t"], c["node_id"]))
    for k in split_map: split_map[k].sort(key=lambda x: x[0])

    used_ids = set(segments["_id"].astype(int))
    new_rows, seg_mapping = [], {}
    coords = {int(r["_id"]): latlon_to_xy(r["lat"], r["long"], HCMUS["lat"]) for _, r in nodes.iterrows()}

    for _, r in segments.iterrows():
        old_id, a, b = int(r["_id"]), int(r["s_node_id"]), int(r["e_node_id"])
        key = tuple(sorted([a, b]))
        if key not in split_map:
            new_rows.append(r.to_dict()); seg_mapping[old_id] = [old_id]
            continue

        ordered = [a] + [x[1] for x in split_map[key]] + [b]
        tot_geom = sum(math.hypot(coords[ordered[i+1]][0] - coords[ordered[i]][0], coords[ordered[i+1]][1] - coords[ordered[i]][1])
                       for i in range(len(ordered)-1) if ordered[i] in coords and ordered[i+1] in coords)
        orig_len = float(r.get("length", np.nan))
        child_ids = []

        for i in range(len(ordered)-1):
            n1, n2 = ordered[i], ordered[i+1]
            new_id = old_id if i == 0 else max(used_ids) + 1
            while new_id in used_ids: new_id += 1
            used_ids.add(new_id)
            child_ids.append(new_id)

            nr = r.to_dict()
            nr.update({"_id": new_id, "s_node_id": n1, "e_node_id": n2})
            if n1 in coords and n2 in coords:
                c_geom = math.hypot(coords[n2][0] - coords[n1][0], coords[n2][1] - coords[n1][1])
                nr["length"] = (orig_len * c_geom / tot_geom) if pd.notna(orig_len) and tot_geom > 0 else c_geom
            new_rows.append(nr)
        seg_mapping[old_id] = child_ids

    res = pd.DataFrame(new_rows)[[c for c in segments.columns if c in pd.DataFrame(new_rows).columns]]
    print(f"Segments split: {len(segments)} -> {len(res)}")
    return res, seg_mapping

def update_mapped_df(df, mapping, col="segment_id"):
    if col not in df.columns: return df.copy()
    rows = []
    for _, r in df.iterrows():
        try: old_id = int(r[col])
        except: rows.append(r.to_dict()); continue
        for cid in mapping.get(old_id, [old_id]):
            nr = r.to_dict()
            nr[col] = cid
            rows.append(nr)
    return pd.DataFrame(rows, columns=df.columns)

def filter_streets(streets, segments):
    if "street_id" not in segments.columns: return streets.copy()
    s_ids = set(pd.to_numeric(segments["street_id"], errors="coerce").dropna().astype(int))
    return streets[pd.to_numeric(streets["_id"], errors="coerce").isin(s_ids)].copy()

def save_files(dfs):
    OUTPUT_DIR.mkdir(exist_ok=True)
    for df, f in zip(dfs, FILES):
        df.to_csv(OUTPUT_DIR / f, index=False)
        print(f"[OK] output/{f}")

# ============================================================
# GRAPH & VISUALIZATION
# ============================================================
def build_graph(nodes, segments):
    G = nx.DiGraph()
    for _, r in nodes.iterrows(): G.add_node(int(r["_id"]), lat=float(r["lat"]), lon=float(r["long"]))
    for _, r in segments.iterrows():
        s, e = int(r["s_node_id"]), int(r["e_node_id"])
        if s not in G or e not in G: continue
        length = float(r.get("length", 1.0))
        length = length if np.isfinite(length) and length > 0 else 1.0
        attrs = {"weight": length, "length": length, "segment_id": int(r["_id"])}
        for c in ["street_id", "max_velocity", "street_level", "street_type", "street_name"]:
            if c in r.index: attrs[c] = None if pd.isna(r[c]) else r[c]
        G.add_edge(s, e, **attrs)
    return G

def get_special_nodes(nodes, hospitals):
    res = []
    for it in [{"name": HCMUS["name"], "lat": HCMUS["lat"], "lon": HCMUS["lon"], "type": "school"}] + \
                [{"name": h["name"], "lat": h["lat"], "lon": h["lon"], "type": "hospital"} for h in hospitals]:
        nid = int(nodes.loc[((nodes["lat"] - it["lat"])**2 + (nodes["long"] - it["lon"])**2).idxmin(), "_id"])
        res.append({**it, "node_id": nid})
    return res

def check_connectivity(G, special_nodes):
    comps = sorted(list(nx.connected_components(G.to_undirected())), key=len, reverse=True)
    print(f"\nSố connected components: {len(comps)}")
    for item in special_nodes:
        cid = next((i for i, c in enumerate(comps) if item["node_id"] in c), None)
        print(f"  {item['name']}: node {item['node_id']}, component {cid}")

def draw_graph(nodes, segments, special_nodes, radius):
    nmap = nodes.set_index("_id")[["long", "lat"]].to_dict("index")
    edges = list({tuple(sorted([int(r["s_node_id"]), int(r["e_node_id"])])) for _, r in segments.iterrows()})
    
    fig, ax = plt.subplots(figsize=(16, 14))
    for s, e in edges:
        if s in nmap and e in nmap:
            ax.plot([nmap[s]["long"], nmap[e]["long"]], [nmap[s]["lat"], nmap[e]["lat"]], lw=0.45, alpha=0.35, color='gray', zorder=1)
            
    ax.scatter(nodes["long"], nodes["lat"], s=4, alpha=0.30, zorder=2)
    for it in special_nodes:
        ax.scatter(it["lon"], it["lat"], s=130 if it["type"] == "school" else 90, zorder=10)
        ax.annotate(f"{it['name']}\n(node {it['node_id']})", (it["lon"], it["lat"]), xytext=(8,8), textcoords="offset points", fontsize=9, fontweight="bold", zorder=11)
        
    ax.set_title(f"Đồ thị giao thông HCMUS và {NUMBER_OF_HOSPITALS} bệnh viện gần nhất\nRadius = {radius:.3f} km", fontsize=15, fontweight="bold")
    ax.grid(True, alpha=0.15)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=300, bbox_inches="tight")
    print(f"[OK] {OUTPUT_IMAGE}")
    plt.show()

# ============================================================
# MAIN
# ============================================================
def main():
    print("=== HCMUS EMERGENCY ROUTING GRAPH - V2 ===")
    check_files()
    nodes, segments, streets, segment_status, train = load_data()
    hospitals, radius = find_nearest_hospitals()
    
    f_segments = filter_segments(nodes, segments, radius)
    f_nodes = filter_nodes(nodes, f_segments)
    
    f_segments, mapping = split_segments(f_nodes, f_segments)
    f_nodes = filter_nodes(nodes, f_segments)
    f_streets = filter_streets(streets, f_segments)
    f_status = update_mapped_df(segment_status, mapping, "segment_id")
    f_train = update_mapped_df(train, mapping, "segment_id")
    
    save_files([f_nodes, f_segments, f_streets, f_status, f_train])
    
    G = build_graph(f_nodes, f_segments)
    sp_nodes = get_special_nodes(f_nodes, hospitals)
    check_connectivity(G, sp_nodes)
    draw_graph(f_nodes, f_segments, sp_nodes, radius)
    print("=== HOÀN TẤT ===")

if __name__ == "__main__":
    main()