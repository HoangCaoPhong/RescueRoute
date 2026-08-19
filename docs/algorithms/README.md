# Tài liệu thuật toán

## English

Each documentation directory follows the corresponding source algorithm name.
Documents should explain the objective, input/output, data structures,
pseudocode, complexity, limitations, and verification strategy.

```text
docs/algorithms/
├── astar/                  ┐
├── bfs/                    │ two-location search
├── dfs/                    │
├── dijkstra/               │
├── ucs/                    ┘
├── genetic_algorithm/      ┐
├── held_karp/              │ multi-location optimization
├── hill_climbing/          │
├── nearest_neighbor/       │
└── simulated_annealing/    ┘
```

Do not copy implementation source into README files. Pseudocode should explain
only the core logic; implementation details belong in
`backend/app/algorithms/`. Reproducible benchmarks must record the dataset,
cost profile, input, seed, and runtime environment.

---

## Tiếng Việt

Mỗi thuật toán dùng cùng tên thư mục với source. Tài liệu tập trung vào mục
tiêu, input/output, cấu trúc dữ liệu, pseudocode, độ phức tạp, giới hạn và cách
kiểm tra.

```text
docs/algorithms/
├── astar/                  ┐
├── bfs/                    │ tìm đường hai điểm
├── dfs/                    │
├── dijkstra/               │
├── ucs/                    ┘
├── genetic_algorithm/      ┐
├── held_karp/              │ tối ưu nhiều điểm
├── hill_climbing/          │
├── nearest_neighbor/       │
└── simulated_annealing/    ┘
```

Không sao chép nguyên mã nguồn vào README. Pseudocode chỉ nên mô tả logic cốt
lõi; chi tiết triển khai nằm trong `backend/app/algorithms/`. Kết quả benchmark
phải ghi dataset, cost profile, input, seed và môi trường chạy để có thể tái
lập.
