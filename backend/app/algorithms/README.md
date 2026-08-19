# Thuật toán

## English

Algorithms in this directory are framework-free Python. They must not depend
on FastAPI, pandas, databases, or the frontend.

| Group | Algorithms |
| --- | --- |
| `graph_search/` | BFS, DFS, UCS, Dijkstra, A* |
| `optimization/` | Hill Climbing, Nearest Neighbor, Held-Karp, Genetic Algorithm, Simulated Annealing |

Hill Climbing is used for two-location routing but remains under optimization
because it is a local-search method.

Two-location algorithms receive a graph, start node, goal node, and optional
cost/heuristic settings. Successful results share `path`, `visited_order`,
`trace_history`, route metrics, timing, optimality, and explanation fields. On
no-route cases, graph-search methods raise `SearchFailure` with a partial trace
in `error.result`. Randomized algorithms must accept a caller-provided `seed`.

When adding or changing an algorithm, reuse the shared graph/cost/trace helpers,
add mirrored tests under `backend/tests/unit/algorithms/`, update the design
documentation, and run focused tests before the full backend suite.

---

## Tiếng Việt

Các thuật toán trong thư mục này là Python thuần, không phụ thuộc FastAPI,
pandas, database hoặc giao diện.

## Phân nhóm

| Nhóm | Thuật toán |
| --- | --- |
| `graph_search/` | BFS, DFS, UCS, Dijkstra, A* |
| `optimization/` | Hill Climbing, Nearest Neighbor, Held–Karp, Genetic Algorithm, Simulated Annealing |

Hill Climbing đang được dùng cho bài toán tìm đường hai điểm nhưng được đặt
trong nhóm optimization vì là local search.

## Contract chung

Thuật toán tìm đường nhận graph, node bắt đầu, node đích và tùy chọn cost hoặc
heuristic. Kết quả thành công dùng cùng nhóm field:

- `path`, `visited_order`, `trace_history`;
- `total_distance`, `estimated_time`, `total_cost`;
- `explored_nodes`, `processing_time_ms`, `is_optimal`;
- `explanation_data`.

Khi không có đường, thuật toán graph search ném `SearchFailure` và đính kèm
partial trace trong `error.result`. Thuật toán có yếu tố ngẫu nhiên phải nhận
`seed` từ caller.

## Thêm hoặc sửa thuật toán

1. Giữ entry point trong đúng folder thuật toán.
2. Dùng helper và trace contract chung; không sao chép graph/cost model.
3. Thêm test đối xứng dưới `backend/tests/unit/algorithms/`.
4. Cập nhật README triển khai và tài liệu trong `docs/algorithms/` khi thay đổi
   giả định hoặc bảo đảm tối ưu.
5. Chạy nhóm test hẹp trước khi chạy toàn bộ backend tests.
