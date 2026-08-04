import time
from typing import Any, Dict, List, Set, Tuple


class NoRouteFoundException(Exception):
    """Ngoại lệ khi không tìm thấy lộ trình giữa start và goal."""
    pass


class SearchResult:
    """Kết quả trả về chuẩn của thuật toán tìm đường trong RescueRoute."""
    def __init__(
        self,
        path: List[str],
        visited_order: List[str],
        frontier_steps: List[List[str]],
        total_distance: float,
        estimated_time: float,
        total_cost: float,
        explored_nodes: int,
        processing_time_ms: float,
        is_optimal: bool,
        explanation: str
    ):
        self.path = path
        self.visited_order = visited_order
        self.frontier_steps = frontier_steps
        self.total_distance = total_distance
        self.estimated_time = estimated_time
        self.total_cost = total_cost
        self.explored_nodes = explored_nodes
        self.processing_time_ms = processing_time_ms
        self.is_optimal = is_optimal
        self.explanation = explanation


def solve_dfs(
    graph: Any,
    start_node_id: str,
    goal_node_id: str,
    cost_profile: Any = None
) -> SearchResult:
    """
    Thuật toán Depth-First Search (DFS) tìm đường trên đồ thị RescueRoute.
    
    Args:
        graph: Đồ thị chứa thông tin nút và cạnh.
        start_node_id: Mã ID nút xuất phát.
        goal_node_id: Mã ID nút đích.
        cost_profile: Profile trọng số tính toán chi phí tuyến đường.
        
    Returns:
        SearchResult chứa chi tiết tuyến đường và dữ liệu phục vụ mô phỏng UI.
    """
    start_time = time.perf_counter()
    
    # Kiểm tra nút đầu vào hợp lệ
    if not graph.has_node(start_node_id) or not graph.has_node(goal_node_id):
        raise NoRouteFoundException(f"Node start '{start_node_id}' hoặc goal '{goal_node_id}' không tồn tại trong đồ thị.")
        
    # Stack chứa các tuple: (current_node_id, path_so_far)
    stack: List[Tuple[str, List[str]]] = [(start_node_id, [start_node_id])]
    visited_order: List[str] = []
    frontier_steps: List[List[str]] = []
    explored_set: Set[str] = set()
    
    while stack:
        # Ghi nhận trạng thái Stack cho frontend mô phỏng (frontier animation)
        frontier_steps.append([node_id for node_id, _ in stack])
        
        current_node, path = stack.pop()
        
        if current_node in explored_set:
            continue
            
        explored_set.add(current_node)
        visited_order.append(current_node)
        
        # Kiểm tra điều kiện dừng (đã đạt mốc đích)
        if current_node == goal_node_id:
            end_time = time.perf_counter()
            processing_time_ms = (end_time - start_time) * 1000.0
            
            # Tính toán chỉ số tổng tuyến đường từ path
            total_distance, estimated_time, total_cost = graph.calculate_path_metrics(path, cost_profile)
            
            return SearchResult(
                path=path,
                visited_order=visited_order,
                frontier_steps=frontier_steps,
                total_distance=total_distance,
                estimated_time=estimated_time,
                total_cost=total_cost,
                explored_nodes=len(explored_set),
                processing_time_ms=processing_time_ms,
                is_optimal=False,
                explanation="DFS tìm thấy tuyến đường theo chiều sâu. Tuyến đường không đảm bảo tính tối ưu nhất."
            )
            
        # Lấy danh sách cạnh đi ra từ node hiện tại
        neighbors = graph.get_neighbors(current_node)
        
        # Sắp xếp các cạnh theo v ID giảm dần để khi POP ra từ Stack (LIFO) sẽ theo thứ tự tăng dần
        neighbors_sorted = sorted(neighbors, key=lambda edge: str(edge.v), reverse=True)
        
        for edge in neighbors_sorted:
            neighbor_id = str(edge.v)
            if neighbor_id not in explored_set:
                stack.append((neighbor_id, path + [neighbor_id]))
                
    end_time = time.perf_counter()
    raise NoRouteFoundException(f"Không tìm thấy đường đi từ '{start_node_id}' đến '{goal_node_id}'.")
