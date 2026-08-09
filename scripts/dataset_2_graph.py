import os
import pandas as pd
from collections import defaultdict, deque
from datetime import datetime
import geopandas as gpd
import enrich_data

# load dataset
def read():
    dataset_path = os.path.join(os.path.dirname(__file__), '../data/processed')

    df_nodes = pd.read_csv(os.path.join(dataset_path, 'nodes_with_poi_labels.csv'))
    df_train = pd.read_csv(os.path.join(dataset_path, 'processed_train.csv'))
    df_base = pd.read_csv(os.path.join(dataset_path, 'base_segments.csv'))

    return df_nodes, df_train, df_base


# cost function
def calc_cost(time, congestion, risk, parameters=(0.648, 0.23, 0.122)):
    return parameters[0]*time + parameters[1]*(congestion**2) + parameters[2]*(risk**2)


# get 3 nearby periods (prev, current, next)
def get_nearby_periods():
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

# processed data to graph data
def build_graph(df_base, df_train):
    nearby_periods = get_nearby_periods()
    print(f"Filtering traffic data for nearby periods: {nearby_periods}")
    
    df_train_filtered = df_train[df_train['period'].isin(nearby_periods)].copy()
    
    if not df_train_filtered.empty:
        df_train_filtered['cost'] = df_train_filtered.apply(
            lambda row: calc_cost(row['time'], row['congestion_factor'], row['risk_factor']), axis=1
        )
        agg_train = df_train_filtered.groupby(['s_node_id', 'e_node_id'])['cost'].mean().reset_index()
    else:
        agg_train = pd.DataFrame(columns=['s_node_id', 'e_node_id', 'cost'])

    graph = defaultdict(dict)
    
    # 1. Add base edges
    for _, row in df_base.iterrows():
        u = row['s_node_id']
        v = row['e_node_id']
        w = row['base_cost']
        graph[u][v] = w
        
    # 2. Overwrite with dynamic traffic cost where available
    for _, row in agg_train.iterrows():
        u = row['s_node_id']
        v = row['e_node_id']
        w = row['cost']
        graph[u][v] = w
        
    return graph


# implement Searching algorithms
def Breadth_First_Search(graph, start, goal):
    visited = set()
    queue = deque([(start, [start])])

    while queue:
        vertex, path = queue.popleft()
        if vertex not in visited:
            if vertex == goal:
                return path
            visited.add(vertex)
            for neighbor in graph.get(vertex, {}):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
    return path


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


# Example usage
def main():
    # enrich data
    if not os.path.exists(os.path.join(os.path.dirname(__file__), '../data/processed/base_segments.csv')):
        print("Base segments data not found. Enriching data...")
        enrich_data.enrich_segments()

    df_nodes, df_train, df_base = read()

    graph = build_graph(df_base, df_train)

    # Pick nodes that actually exist in the filtered graph
    valid_nodes = list(graph.keys())
    #print("Valid nodes in the graph:", valid_nodes)
    if len(valid_nodes) < 2:
        print("Not enough nodes in the graph for the current period.")
        return

    # for i in range(len(valid_nodes)):
    #     start_node = valid_nodes[i]
    #     for j in range(len(valid_nodes)):
    #         if i != j:
    #             goal_node = valid_nodes[j]
    #             path = Breadth_First_Search(graph, start_node, goal_node)
    #             print(f"BFS Path from {start_node} to {goal_node}:", path)

    start_node = valid_nodes[0]
    goal_node = valid_nodes[20]

    path = Breadth_First_Search(graph, start_node, goal_node)
    print("BFS Path:", path)


if __name__ == "__main__":
    main()