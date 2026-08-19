# Uniform Cost Search (UCS)

## English

Entry point:

```python
solve_ucs(graph, start_node_id, goal_node_id,
          cost_profile=None, edge_cost=None)
```

UCS always expands the node with the smallest accumulated cost `g(n)`. Frontier
items expose `node_id`, `g`, `h=0`, `f=g`, and `priority` for consistent A*
visualization.

- Complete and optimal with finite, non-negative edge costs.
- Uses lazy deletion to ignore stale heap entries.
- Deterministic for the same input and neighbor order.
- Raises `SearchFailure` with a partial trace when no route exists.

Tests: `backend/tests/unit/algorithms/graph_search/ucs/`.

---

## Tiếng Việt

Entry point:

```python
solve_ucs(graph, start_node_id, goal_node_id,
          cost_profile=None, edge_cost=None)
```

UCS luôn mở rộng node có accumulated cost `g(n)` nhỏ nhất. Frontier dùng các
field `node_id`, `g`, `h=0`, `f=g` và `priority` để frontend hiển thị thống
nhất với A*.

## Bảo đảm

- Hoàn chỉnh và tối ưu khi edge cost hữu hạn, không âm.
- Bỏ qua heap entry cũ bằng lazy deletion.
- Kết quả xác định với cùng input và thứ tự neighbor.
- Khi không có đường, ném `SearchFailure` kèm partial trace.

Test: `backend/tests/unit/algorithms/graph_search/ucs/`.
