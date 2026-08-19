# Hill Climbing

## English

Entry point:

```python
solve_hill_climbing(graph, start_node_id, goal_node_id, heuristic,
                    cost_profile=None, edge_cost=None,
                    allow_sideways=False, max_steps=None)
```

At each step, Hill Climbing selects the unvisited neighbor with the lowest
heuristic. Stable node representation breaks ties, while `allow_sideways`
controls movement across plateaus.

- Fast and deterministic, but incomplete and not globally optimal.
- May stop at a local optimum, plateau, dead end, or step limit.
- Heuristic values must be finite, non-negative, and objective-consistent.
- `heuristic_steps` records local choices for UI explanations.

Tests: `backend/tests/unit/algorithms/optimization/hill_climbing/`.

---

## Tiếng Việt

Entry point:

```python
solve_hill_climbing(graph, start_node_id, goal_node_id, heuristic,
                    cost_profile=None, edge_cost=None,
                    allow_sideways=False, max_steps=None)
```

Tại mỗi bước, thuật toán chọn neighbor chưa thăm có heuristic nhỏ nhất. Tie
được giải bằng biểu diễn node ổn định; tùy chọn `allow_sideways` cho phép đi
ngang trên plateau.

- Nhanh và xác định nhưng không complete, không tối ưu toàn cục.
- Có thể dừng ở local optimum, plateau, dead end hoặc step limit.
- Heuristic phải hữu hạn, không âm và nhất quán với mục tiêu định tuyến.
- `heuristic_steps` ghi lại lựa chọn cục bộ để giải thích trên UI.

Test: `backend/tests/unit/algorithms/optimization/hill_climbing/`.
