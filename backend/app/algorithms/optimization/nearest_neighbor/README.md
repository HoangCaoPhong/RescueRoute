# Nearest Neighbor

## English

Entry point:

```python
optimize_nearest_neighbor(start_node_id, waypoint_ids,
                          goal_node_id, pair_costs)
```

The method repeatedly selects the cheapest reachable unvisited waypoint from
the current location, then connects the final waypoint to the fixed goal.

- `O(k²)` after the pairwise matrix is available.
- Deterministic, with stable ID-based tie-breaking.
- Guaranteed optimal only with at most one waypoint.
- Raises `ValueError` when a remaining waypoint or the goal is unreachable.

Tests: `backend/tests/unit/algorithms/optimization/nearest_neighbor/`.

---

## Tiếng Việt

Entry point:

```python
optimize_nearest_neighbor(start_node_id, waypoint_ids,
                          goal_node_id, pair_costs)
```

Thuật toán lần lượt chọn waypoint chưa thăm có pairwise cost nhỏ nhất từ điểm
hiện tại, sau đó nối waypoint cuối tới goal cố định.

- Độ phức tạp sau khi có cost matrix: `O(k²)`.
- Xác định; tie được giải bằng biểu diễn ID ổn định.
- Chỉ bảo đảm tối ưu khi có không quá một waypoint.
- Ném `ValueError` nếu không thể tới một waypoint còn lại hoặc goal.

Test: `backend/tests/unit/algorithms/optimization/nearest_neighbor/`.
