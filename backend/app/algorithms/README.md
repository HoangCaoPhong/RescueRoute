# Algorithms workspace

Mỗi thuật toán có một folder riêng để thành viên có thể code, test và review độc lập. Thuật toán trong đây là Python thuần: không import FastAPI, Supabase, Leaflet hoặc gọi API bên ngoài.

## Phân nhóm và owner hiện tại

| Nhóm | Folder | Thuật toán | Owner | Branch đề xuất |
|---|---|---|---|---|
| Graph search | `graph_search/astar/` | A* Search | Phong | `feature/astar-search` |
| Graph search | `graph_search/bfs/` | Breadth-First Search | Ngọc | `feature/bfs-search` |
| Graph search | `graph_search/dfs/` | Depth-First Search | Kiên | `feature/dfs-search` |
| Graph search | `graph_search/dijkstra/` | Dijkstra | Hòa | `feature/dijkstra-search` |
| Graph search | `graph_search/ucs/` | Uniform Cost Search | Nhân | `feature/ucs-search` |
| Optimization | `optimization/hill_climbing/` | Hill Climbing | Phong | `feature/hill-climbing` |
| Optimization | `optimization/simulated_annealing/` | Simulated Annealing | Nhân | `feature/simulated-annealing` |
| Optimization | `optimization/nearest_neighbor/` | Nearest Neighbor | Shared | `temp/trace-history-merge-dev` |
| Optimization | `optimization/held_karp/` | Held-Karp Dynamic Programming | Shared | `temp/trace-history-merge-dev` |

## Cấu trúc chuẩn của một folder

Khi bắt đầu implementation, thành viên thêm file theo nhu cầu:

```text
<algorithm>/
├── README.md          # Mục tiêu, giả định và checklist có sẵn
├── __init__.py        # Public export của thuật toán
├── algorithm.py       # Entry point chính
└── helpers.py         # Chỉ tạo nếu logic phụ đủ lớn để tách
```

Không bắt buộc tạo `helpers.py`. A* có thể dùng `heuristic.py`; Genetic Algorithm có thể dùng `operators.py` và `population.py`. Tránh tạo nhiều file rỗng chỉ để giống cây mẫu.

## Contract chung

Graph-search algorithms phải dùng cùng input và trả cùng một SearchResult. Tối thiểu cần có:

```text
Input:
- graph
- start_node_id
- goal_node_id
- cost_profile
- optional heuristic/config

Output:
- path
- visited_order
- frontier_steps/search_events
- total_distance
- estimated_time
- total_cost
- explored_nodes
- processing_time_ms
- is_optimal
- explanation data
```

Optimization algorithms cho nhiều điểm phải trả thêm visiting order và nhận `seed` nếu có yếu tố ngẫu nhiên.

Contract chính xác sẽ nằm trong domain/algorithm common modules sau khi `feature/graph-search-contract` được merge. Không tự tạo contract tạm chỉ dùng riêng cho folder của mình.

## Quy trình cho một thành viên

1. Đồng bộ `dev` và tạo branch ghi trong bảng owner.
2. Đọc README trong folder thuật toán được giao.
3. Đọc contract chung và dataset mẫu.
4. Viết design, pseudocode và flowchart trong `docs/algorithms/`.
5. Implement trong `algorithm.py`; giữ entry point nhỏ và có type hints.
6. Viết unit test trong folder đối xứng dưới `backend/tests/unit/algorithms/`.
7. Chạy test, ghi benchmark tối thiểu và tự review diff.
8. Mở pull request vào `dev`, không vào `main`.

## Definition of Done cho thuật toán

- Dùng đúng Graph, cost và result contract chung.
- Không gọi mạng/database và không sửa graph đầu vào.
- Có test: đường hợp lệ, không có đường, start bằng goal, đồ thị có hướng và cạnh bị chặn/rủi ro cao.
- Có `visited_order` và search events đủ cho frontend mô phỏng.
- Có giải thích tính complete/optimal/approximate trong README hoặc tài liệu thiết kế.
- Thuật toán ngẫu nhiên nhận seed và test tái lập được.
- Có số liệu chạy trên cùng dataset mẫu để so sánh công bằng.
