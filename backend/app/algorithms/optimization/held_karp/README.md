# Held–Karp

## English

Entry point:

```python
optimize_held_karp(start_node_id, waypoint_ids, goal_node_id, pair_costs)
```

Held-Karp uses dynamic programming over `(visited_mask, last_waypoint)` to find
the minimum-cost waypoint order with fixed start and goal locations.

- Time complexity: `O(k² 2ᵏ)`.
- State complexity: `O(k 2ᵏ)`.
- Current limit: at most 10 waypoints.
- Exact for the supplied matrix; it does not compute pairwise paths itself.
- Raises `ValueError` if a complete visit order cannot reach the goal.

Tests: `backend/tests/unit/algorithms/optimization/held_karp/`.

---

## Tiếng Việt

Entry point:

```python
optimize_held_karp(start_node_id, waypoint_ids, goal_node_id, pair_costs)
```

Thuật toán dùng dynamic programming trên trạng thái
`(visited_mask, last_waypoint)` để tìm thứ tự waypoint có tổng pairwise cost
nhỏ nhất, với start và goal cố định.

- Độ phức tạp thời gian: `O(k² 2ᵏ)`.
- Số trạng thái: `O(k 2ᵏ)`.
- Giới hạn hiện tại: tối đa 10 waypoint.
- Tối ưu trên matrix được cung cấp; không tự tính đường giữa từng cặp.
- Ném `ValueError` khi không thể ghé đủ điểm rồi tới goal.

Test: `backend/tests/unit/algorithms/optimization/held_karp/`.
