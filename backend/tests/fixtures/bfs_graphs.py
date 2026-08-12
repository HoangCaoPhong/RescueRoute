# Graph with two possible paths.
# BFS should choose A -> B -> D because it has fewer hops.

MINIMUM_HOP_GRAPH = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["E"],
    "D": [],
    "E": ["D"],
}

# Directed graph used to verify one-way edges.
DIRECTED_GRAPH = {
    "A": ["B"],
    "B": []
}

# Graph containing an unreachable node C.
NO_PATH_GRAPH = {
    "A": ["B"],
    "B": [],
    "C": []
}

# Graph where node D can be discovered from B and C.
DUPLICATE_DISCOVERY_GRAPH = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["D"],
    "D": []
}