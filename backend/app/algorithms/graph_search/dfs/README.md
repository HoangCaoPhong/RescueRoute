# Depth-First Search (DFS)

## English

Entry points:

```python
solve_dfs(graph, start_node_id, goal_node_id, cost_profile=None)
solve_depth_limited_dfs(graph, start_node_id, goal_node_id,
                        max_depth=None, max_expansions=5000)
```

DFS uses a LIFO stack to explore one branch deeply. The bounded variant supports
`max_depth` and `max_expansions`; `solve_bounded_dfs` is its alias.

- A visited set prevents cycles.
- Neighbor processing is deterministic.
- DFS does not guarantee minimum hops, distance, time, or cost.
- Search may stop because the frontier is empty or a configured limit is met.
- Failure results retain a partial trace in `SearchFailure.result`.

Tests: `backend/tests/unit/algorithms/graph_search/dfs/`.

---

## Tiếng Việt

Các entry point:

```python
solve_dfs(graph, start_node_id, goal_node_id, cost_profile=None)
solve_depth_limited_dfs(graph, start_node_id, goal_node_id,
                        max_depth=None, max_expansions=5000)
```

DFS dùng ngăn xếp LIFO để đi sâu theo từng nhánh. Biến thể giới hạn hỗ trợ
`max_depth` và `max_expansions`, phù hợp với graph lớn hoặc môi trường ít bộ nhớ.
`solve_bounded_dfs` là alias của biến thể này.

## Bảo đảm và giới hạn

- Có phát hiện node đã thăm để tránh vòng lặp.
- Xử lý neighbor theo thứ tự xác định.
- Không bảo đảm tuyến ngắn nhất hoặc cost thấp nhất.
- Có thể dừng vì hết frontier, đạt độ sâu hoặc đạt số lần mở rộng tối đa.
- Lỗi tìm kiếm giữ lại partial trace trong `SearchFailure.result`.

Test: `backend/tests/unit/algorithms/graph_search/dfs/`.
