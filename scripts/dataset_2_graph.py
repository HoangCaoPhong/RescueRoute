import os
import pandas as pd
from collections import defaultdict
from datetime import datetime
import geopandas as gpd
import osmnx as ox
import numpy as np
from scipy.spatial import cKDTree

# load dataset
def read():
    dataset_path = os.path.join(os.path.dirname(__file__), 'dataset')

    df_nodes = pd.read_csv(os.path.join(dataset_path, 'nodes.csv'))
    df_segment_status = pd.read_csv(os.path.join(dataset_path, 'segment_status.csv'))
    df_segments = pd.read_csv(os.path.join(dataset_path, 'segments.csv'))
    df_streets = pd.read_csv(os.path.join(dataset_path, 'streets.csv'))
    df_train = pd.read_csv(os.path.join(dataset_path, 'train.csv'))

    return df_nodes, df_segment_status, df_segments, df_streets, df_train


# LOS dictionary
LOS_dict = {
    'A': 1.0,
    'B': 1.0,
    'C': 2.0,
    'D': 3.0,
    'E': 5.0,
    'F': 8.0
}


# cost function
def calc_actual_velocity(df_train, LOS_dict):
    return 70.0 / LOS_dict[df_train['LOS']]

def calc_cost(time, congestion, risk):
    return 0.5*time + 0.3*(congestion**2) + 0.2*(risk**2)


# datetime.now() to period
def time2period():
    current_time = datetime.now().time()
    
    hour = current_time.hour
    min = current_time.minute
    if min < 15:
        return f"period_{hour}_00"
    elif min < 45:
        return f"period_{hour}_30"
    else:
        next_hour = (hour + 1) % 24
        return f"period_{next_hour}_00"

# raw data to graph data
def build_graph(df_train, LOS_dict):
    period_now = time2period()
    df_train = df_train[df_train['period'] == period_now]
    df_train['actual_velocity'] = df_train.apply(calc_actual_velocity, axis=1, LOS_dict=LOS_dict)
    df_train['time'] = df_train['length'] / df_train['actual_velocity']
    df_train['cost'] = df_train.apply(lambda row: calc_cost(row['time'], LOS_dict[row['LOS']], row['street_level']), axis=1)

    graph = defaultdict(dict)
    for _, row in df_train.iterrows():
        u = row['s_node_id']
        v = row['e_node_id']
        w = row['cost']

        graph[u][v] = w


# implement Searching algorithms
def Breadth_First_Search(graph, start, goal):
    visited = set()
    queue = [(start, [start])]

    while queue:
        (vertex, path) = queue.pop(0)
        if vertex not in visited:
            if vertex == goal:
                return path
            visited.add(vertex)
            for neighbor in graph[vertex]:
                queue.append((neighbor, path + [neighbor]))
    return None


def Depth_First_Search(graph, start, goal):
    visited = set()
    stack = [(start, [start])]

    while stack:
        (vertex, path) = stack.pop()
        if vertex not in visited:
            if vertex == goal:
                return path
            visited.add(vertex)
            for neighbor in graph[vertex]:
                stack.append((neighbor, path + [neighbor]))
    return None


def Uniform_Cost_Search(graph, start, goal):
    visited = set()
    queue = [(0, start, [start])]

    while queue:
        (cost, vertex, path) = min(queue)
        queue.remove((cost, vertex, path))
        if vertex not in visited:
            if vertex == goal:
                return path
            visited.add(vertex)
            for neighbor in graph[vertex]:
                total_cost = cost + graph[vertex][neighbor]
                queue.append((total_cost, neighbor, path + [neighbor]))
    return None


def A_Star_Search(graph, start, goal, heuristic):
    visited = set()
    queue = [(0 + heuristic[start], start, [start])]

    while queue:
        (cost, vertex, path) = min(queue)
        queue.remove((cost, vertex, path))
        if vertex not in visited:
            if vertex == goal:
                return path
            visited.add(vertex)
            for neighbor in graph[vertex]:
                total_cost = cost - heuristic[vertex] + graph[vertex][neighbor] + heuristic[neighbor]
                queue.append((total_cost, neighbor, path + [neighbor]))
    return None


print(df_nodes[['long', 'lat']].drop_duplicates().reset_index(drop=True).shape)
print(df_segment_status[df_segment_status['velocity'] == max(df_segment_status['velocity'])])
print(df_streets.shape)
print(df_segments.shape)




# 1. Download HCMC POIs & Traffic Features from OpenStreetMap
tags = {
    'amenity': True,   # Schools, hospitals, banks, parking
    'building': True,  # Offices, commercial plazas
    'tourism': True,   # Landmarks, parks
    'highway': ['traffic_signals', 'motorway_junction', 'bus_stop'] # Relevant for traffic data
}
print("Downloading HCMC POIs from OSM...")
pois_gdf = ox.features_from_place("Ho Chi Minh City, Vietnam", tags=tags)
pois_gdf = pois_gdf[pois_gdf['name'].notnull()][['name', 'geometry']].copy()

# 2. Project POIs to UTM Zone 48N (EPSG:32648) for accurate meter-based distances in HCMC
pois_gdf = pois_gdf.to_crs(epsg=32648)
poi_coords = np.array([(geom.centroid.x, geom.centroid.y) for geom in pois_gdf.geometry])
poi_names = pois_gdf['name'].values

# 3. Build 2D Spatial KD-Tree in memory
tree = cKDTree(poi_coords)

# 4. Real nodes dataset
df_nodes

# Convert node coordinates to meters (EPSG:32648)
nodes_gdf = gpd.GeoDataFrame(
    df_nodes, geometry=gpd.points_from_xy(df_nodes['long'], df_nodes['lat']), crs="EPSG:4326"
).to_crs(epsg=32648)

node_coords = np.array([(geom.x, geom.y) for geom in nodes_gdf.geometry])

# 5. Query nearest POI for all 570,000 nodes in parallel (~1-2 seconds)
distances, indices = tree.query(node_coords, k=1)

# 6. Assign nearest landmark & exact distance in meters back to DataFrame
df_nodes['nearest_location'] = poi_names[indices]
df_nodes['distance_meters'] = np.round(distances, 2)

print(df_nodes.head())