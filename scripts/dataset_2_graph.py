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
    dataset_path = os.path.join(os.path.dirname(__file__), '../data/processed')

    df_nodes = pd.read_csv(os.path.join(dataset_path, 'nodes_with_poi_labels.csv'))
    df_train = pd.read_csv(os.path.join(dataset_path, 'processed_train.csv'))

    return df_nodes, df_train


# cost function
def calc_cost(time, congestion, risk, parameters=(0.648, 0.23, 0.122)):
    return parameters[0]*time + parameters[1]*(congestion**2) + parameters[2]*(risk**2)


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

# processed data to graph data
def build_graph(df_train, LOS_dict):
    period_now = time2period()
    df_train = df_train[df_train['period'] == period_now]
    df_train['cost'] = df_train.apply(lambda row: calc_cost(row['time'], LOS_dict[row['congestion_factor']], row['risk_factor']), axis=1)

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


