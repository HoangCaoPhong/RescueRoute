# Backend tests

Test đặt đối xứng với source để dễ tìm owner và review:

```text
tests/
├── fixtures/                    # Graph/dataset fixture dùng chung
├── integration/                 # Service, repository, API integration
└── unit/
    ├── algorithms/
    │   ├── graph_search/
    │   │   ├── astar/
    │   │   ├── bfs/
    │   │   ├── dfs/
    │   │   ├── dijkstra/
    │   │   └── ucs/
    │   └── optimization/
    │       ├── genetic_algorithm/
    │       ├── hill_climbing/
    │       └── simulated_annealing/
    └── domain/
```

Trong mỗi folder thuật toán, file chính nên là `test_algorithm.py`. Fixture graph dùng chung đặt tại `tests/fixtures/`, không copy graph riêng vào từng test nếu cùng mục đích.

Test thuật toán không gọi API, database hoặc Internet. Benchmark không thay thế assertion về correctness.

