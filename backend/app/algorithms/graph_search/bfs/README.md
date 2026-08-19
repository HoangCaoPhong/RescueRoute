# Breadth-First Search (BFS)

## English

Entry point:

```python
solve_bfs(graph, start_node_id, goal_node_id, cost_profile=None)
```

BFS uses a FIFO queue and marks nodes when they are enqueued. This prevents
duplicate frontier entries and finds a minimum-edge route when all edges are
treated equally.

- `hop_count` reports the number of edges in the route.
- `is_optimal=True` refers only to minimum-hop optimality.
- Distance, travel time, and traffic cost are not optimized.
- Shared helpers provide deterministic neighbor ordering.
- `SearchFailure.result` preserves the partial trace on failure.

Tests: `backend/tests/unit/algorithms/graph_search/bfs/`.

---

## Tiếng Việt

Entry point:

```python
solve_bfs(graph, start_node_id, goal_node_id, cost_profile=None)
```

BFS dùng hàng đợi FIFO và đánh dấu node ngay khi đưa vào hàng đợi. Cách này
tránh frontier trùng lặp và tìm tuyến có số cạnh ít nhất khi mọi cạnh được xem
như nhau.

## Kết quả và giới hạn

- `hop_count` là số cạnh trong tuyến tìm được.
- `is_optimal=True` chỉ có nghĩa tối ưu theo số hop.
- Không bảo đảm tối ưu khoảng cách, thời gian hoặc traffic cost.
- Neighbor được lấy theo thứ tự xác định từ helper chung.
- Khi không có đường, `SearchFailure.result` vẫn chứa visited order và trace.

Test: `backend/tests/unit/algorithms/graph_search/bfs/`.
