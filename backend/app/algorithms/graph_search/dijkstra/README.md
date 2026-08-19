# Dijkstra

## English

Entry point:

```python
solve_dijkstra(graph, start_node_id, goal_node_id,
               cost_profile=None, edge_cost=None)
```

The implementation uses the shared priority-search core with a zero heuristic.
The `edge_cost` callback selects the weight to optimize; the current demo
service supplies physical road distance for Dijkstra.

- Complete and optimal when all reachable weights are finite and non-negative.
- Does not mutate the input graph.
- Returns the shared A*/UCS result and trace shape.
- Raises `SearchFailure` with a partial trace when no route exists.

Tests: `backend/tests/unit/algorithms/graph_search/dijkstra/`.

---

## Tiếng Việt

Entry point:

```python
solve_dijkstra(graph, start_node_id, goal_node_id,
               cost_profile=None, edge_cost=None)
```

Implementation dùng priority search chung với heuristic bằng 0. Callback
`edge_cost` quyết định trọng số cần tối ưu; demo hiện truyền khoảng cách đường
cho Dijkstra.

## Bảo đảm

- Hoàn chỉnh và tối ưu khi mọi trọng số có thể đi tới đều hữu hạn, không âm.
- Không sửa graph đầu vào.
- Trả cùng result/trace contract với A* và UCS.
- Khi không có đường, ném `SearchFailure` kèm partial trace.

Test: `backend/tests/unit/algorithms/graph_search/dijkstra/`.
