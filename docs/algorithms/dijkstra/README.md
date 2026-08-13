# Dijkstra

## Objective

Dijkstra finds the shortest path from a source node to a target node in a graph with non-negative edge weights. In RescueRoute, this algorithm is used to identify the optimal route when the selected edge weight is either road distance or a traffic-configured cost profile.

## Assumptions

- The graph may be directed or undirected and is represented explicitly.
- All edge weights are non-negative.
- The input graph is not modified during execution.
- Optimality is guaranteed whenever edge weights are non-negative.

## Candidate route and objective

- Candidate route: the path from `start_node_id` to `goal_node_id`.
- Objective function: the total route cost, computed as the sum of edge weights according to `resolve_edge_cost`.
- When the weight is distance, the resulting value reflects distance; when it is a traffic cost profile, `total_cost` reflects the configured route cost.

## Algorithm

1. Initialize the distance from the start node to 0 and all other nodes to infinity.
2. Select the unvisited node with the smallest current distance.
3. Examine its neighbors and relax the distances when a better path is found.
4. Continue until all reachable nodes are processed or the goal is reached.
5. Reconstruct the route by walking backward through the parent map.

## Pseudocode

```text
dist[start] = 0
priority_queue = [(0, start)]
parent = {start: None}

while queue is not empty:
    current = node with minimum dist
    if current == goal:
        break
    for neighbor in graph[current]:
        new_cost = dist[current] + edge_cost(current, neighbor)
        if new_cost < dist[neighbor]:
            dist[neighbor] = new_cost
            parent[neighbor] = current
            push(neighbor, new_cost)

return reconstruct_path(parent, goal)
```

## Stop condition

- Stop when the goal node is extracted from the priority queue.
- If no route exists, return a `SearchFailure` with partial trace information.

## Optimality

- The algorithm is fully optimal for graphs with non-negative edge weights.
- It does not require a heuristic because it expands the lowest accumulated cost first.

## Trace and UI

The algorithm records search history using `SearchTraceHistory`, including:
- `visited_order`
- `frontier_steps`
- `trace_history.events`

This is compatible with the UI playback for visited nodes and frontier evolution.

## Example benchmark

- Sample graph: 5–10 nodes with a mix of short and long edges.
- Expected result: the selected path minimizes total cost and avoids unnecessary detours.
- Compared with A* and UCS on the same graph, it yields the same optimal route but differs in expansion order and trace layout.
