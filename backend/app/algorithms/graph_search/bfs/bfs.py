from collections import deque
from time import perf_counter


from backend.app.algorithms.graph_search.utils import (
    reconstruct_path,
    get_neighbors,
    has_node,
    calculate_path_metrics,
)
from backend.app.algorithms.graph_search.trace_history import SearchFailure, SearchTraceHistory


def solve_bfs(graph, start_node_id, goal_node_id, cost_profile=None):
    """
    Breadth-First Search (BFS).

    BFS uses a FIFO queue and explores the graph level by level.

    It guarantees a minimum-hop path when all edges are treated equally.
    It does not optimize distance, travel time, congestion, or traffic cost.
    """

    start_time = perf_counter()

    # Kiểm tra hai node đầu vào trước khi tạo frontier.
    if (not has_node(graph, start_node_id) or not has_node(graph, goal_node_id)):
        raise ValueError(
            f"Start node '{start_node_id}' or "
            f"goal node '{goal_node_id}' does not exist."
        )

    # Hàng đợi FIFO giữ đúng thứ tự duyệt theo từng tầng.
    queue = deque([start_node_id])
    visited = {start_node_id}
    parent = {start_node_id: None}
    
    trace_history = SearchTraceHistory()

    while queue:
        # Chụp frontier ngay trước khi mở rộng node hiện tại.
        current_node = queue[0]
        trace_history.record_expansion(current_node, queue)
        current_node = queue.popleft()

        if current_node == goal_node_id:

            path = reconstruct_path(parent, goal_node_id)
            (total_distance, estimated_time, total_cost) = calculate_path_metrics(graph, path, cost_profile)

            processing_time_ms = (perf_counter() - start_time) * 1000.0

            return {
                "found": True,
                "path": path,
                **trace_history.as_result_fields(),

                "total_distance": total_distance,
                "estimated_time": estimated_time,
                "total_cost": total_cost,

                "explored_nodes": trace_history.explored_nodes,
                "processing_time_ms": processing_time_ms,

                # BFS chỉ tối ưu theo số cạnh khi mọi cạnh ngang nhau.
                "is_optimal": True,

                "explanation_data": {
                    "algorithm": "BFS",
                    "optimality": "minimum_hops",
                    "message": (
                        "BFS finds a path with the minimum number "
                        "of edges when all edges are treated equally. "
                        "It does not guarantee minimum distance, "
                        "travel time, or traffic cost."
                    )
                },

                # BFS-specific additional metric
                "hop_count": len(path) - 1
            }

        for neighbor_node in get_neighbors(graph, current_node):
            if neighbor_node not in visited:
                # Đánh dấu lúc enqueue để một node không xuất hiện hai lần.
                visited.add(neighbor_node)
                parent[neighbor_node] = current_node
                queue.append(neighbor_node)

    # Giữ partial trace để frontend vẫn phát lại được lần tìm thất bại.
    message = f"No route found from '{start_node_id}' to '{goal_node_id}'."
    raise SearchFailure(
        message,
        {
            "found": False,
            "path": [],
            **trace_history.as_result_fields(),
            "explored_nodes": trace_history.explored_nodes,
            "processing_time_ms": (perf_counter() - start_time) * 1000.0,
            "message": message,
        },
    )
