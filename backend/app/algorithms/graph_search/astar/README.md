# A* Search

## English

Entry point:

```python
solve_astar(graph, start_node_id, goal_node_id, heuristic=None,
            cost_profile=None, edge_cost=None,
            heuristic_is_admissible=False)
```

A* expands the node with the lowest `f(n) = g(n) + h(n)`. The heuristic must
be finite, non-negative, and expressed in the same unit as edge cost. Without a
heuristic, the implementation behaves like UCS.

- Complete on a finite graph with finite, non-negative edge costs.
- Optimal without a heuristic or with a proven admissible heuristic.
- Deterministic for the same graph, neighbor order, and callbacks.
- Raises `ValueError` for invalid nodes/costs/heuristics and `SearchFailure`
  when no route exists.

Tests: `backend/tests/unit/algorithms/graph_search/astar/`.

---

## Tiếng Việt

Entry point:

```python
solve_astar(graph, start_node_id, goal_node_id, heuristic=None,
            cost_profile=None, edge_cost=None,
            heuristic_is_admissible=False)
```

A* mở rộng node có `f(n) = g(n) + h(n)` nhỏ nhất. `heuristic` phải trả giá trị
hữu hạn, không âm và cùng đơn vị với edge cost. Nếu không truyền heuristic,
thuật toán tương đương UCS.

## Bảo đảm

- Hoàn chỉnh trên graph hữu hạn với edge cost hữu hạn, không âm.
- Tối ưu khi không dùng heuristic hoặc heuristic được chứng minh admissible.
- Kết quả xác định với cùng graph, thứ tự neighbor và callback.
- Ném `ValueError` cho node/cost/heuristic không hợp lệ và `SearchFailure` khi
  không có đường.

Test: `backend/tests/unit/algorithms/graph_search/astar/`.
