# Depth-First Search (DFS)

- **Owner**: Kiên
- **Branch**: `feature/dfs-search`
- **Test folder**: `backend/tests/unit/algorithms/graph_search/dfs/`
- **Docs folder**: `docs/algorithms/dfs/`

## 1. Mô tả thuật toán đối với Project

Depth-First Search (DFS) trong hệ thống tối ưu hóa lộ trình xe cấp cứu được sử dụng để duyệt toàn bộ đồ thị theo chiều sâu nhằm tìm kiếm đường đi từ điểm xuất phát (Start) đến điểm cấp cứu hoặc bệnh viện (Goal).

### Đặc điểm thuật toán trong RescueRoute:
- **Không đảm bảo tối ưu**: DFS không đảm bảo tìm được đường đi ngắn nhất hoặc có chi phí thấp nhất (`is_optimal = False`).
- **Thứ tự duyệt deterministic (nhất quán)**: Để đảm bảo kết quả kiểm thử tái lập được, các lân cận (neighbors/outgoing edges) của một node sẽ được duyệt theo thứ tự bảng chữ cái của ID node đích (hoặc sắp xếp tăng dần theo ID).
- **Tránh chu trình**: Sử dụng một tập hợp `visited` hoặc `explored` để theo dõi các node đã duyệt qua trên đường đi hiện tại nhằm tránh lặp vô hạn.

---

## 2. Input & Output Contract

### Input:
- `graph`: Đồ thị chứa danh sách các Nodes và Edges.
- `start_node_id`: ID của node xuất phát (str).
- `goal_node_id`: ID của node đích (str).
- `cost_profile`: Profile trọng số ($\alpha, \beta, \gamma$) dùng để tính toán tổng chi phí lộ trình sau khi tìm thấy đường đi.

### Output (`SearchResult`):
- `path`: Danh sách các node ID theo đúng thứ tự từ start đến goal (ví dụ: `['A', 'B', 'H']`).
- `visited_order`: Danh sách các node ID theo thứ tự đã mở rộng (pop ra từ stack).
- `frontier_steps`: Lịch sử các bước tìm kiếm (trạng thái của Stack ở mỗi bước duyệt) phục vụ cho frontend mô phỏng.
- `total_distance`: Tổng khoảng cách của tuyến đường tìm được (mét).
- `estimated_time`: Tổng thời gian di chuyển ước tính (giây).
- `total_cost`: Tổng chi phí của tuyến đường (tính bằng Cost Function chung của dự án).
- `explored_nodes`: Số lượng node đã duyệt.
- `processing_time_ms`: Thời gian chạy thuật toán (mili giây).
- `is_optimal`: Luôn trả về `False` (do bản chất DFS).
- `explanation`: Giải thích cấu trúc (ví dụ: lý do DFS được chọn, hoặc cảnh báo tuyến đường không tối ưu).

---

## 3. Pseudocode (Mã giả)

```python
def solve_dfs(graph, start_node_id, goal_node_id, cost_profile) -> SearchResult:
    # 1. Khởi tạo
    stack = [(start_node_id, [start_node_id])] # Lưu cặp (node_hiện_tại, path_đến_node_đó)
    visited_order = []
    frontier_steps = []
    explored_set = set()
    
    # 2. Vòng lặp duyệt
    while stack is not None and len(stack) > 0:
        # Lưu trạng thái stack cho frontend simulation
        frontier_steps.append([node for node, _ in stack])
        
        current_node, path = stack.pop()
        
        if current_node in explored_set:
            continue
            
        explored_set.add(current_node)
        visited_order.append(current_node)
        
        # Kiểm tra đích
        if current_node == goal_node_id:
            # Tính toán các thông số khoảng cách, thời gian, chi phí dựa trên path tìm được
            total_distance, estimated_time, total_cost = calculate_metrics(path, graph, cost_profile)
            return SearchResult(
                path=path,
                visited_order=visited_order,
                frontier_steps=frontier_steps,
                total_distance=total_distance,
                estimated_time=estimated_time,
                total_cost=total_cost,
                explored_nodes=len(explored_set),
                is_optimal=False,
                explanation="DFS tìm thấy tuyến đường nhưng không đảm bảo đây là phương án tối ưu nhất."
            )
            
        # Lấy danh sách cạnh đi ra và sắp xếp theo ID đích tăng dần để đảm bảo tính nhất quán (deterministic)
        neighbors = graph.get_neighbors(current_node)
        neighbors.sort(key=lambda edge: edge.v, reverse=True) # Sắp xếp ngược vì stack là LIFO
        
        for edge in neighbors:
            neighbor_node = edge.v
            if neighbor_node not in explored_set:
                stack.append((neighbor_node, path + [neighbor_node]))
                
    raise NoRouteFoundException("Không tìm thấy đường đi từ start đến goal.")
```

