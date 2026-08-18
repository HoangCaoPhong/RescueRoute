# Tài liệu thuật toán

Mỗi thuật toán tạo một folder cùng tên với source:

```text
docs/algorithms/
├── astar/
├── bfs/
├── dfs/
├── dijkstra/
├── ucs/
├── held_karp/
├── hill_climbing/
├── nearest_neighbor/
└── simulated_annealing/
```

Nội dung đề xuất trong mỗi folder:

```text
<algorithm>/
├── design.md        # Ý tưởng, input/output, data structure, complexity
├── pseudocode.md    # Pseudocode do nhóm tự viết
├── flowchart.mmd    # Mermaid source cho flowchart
└── benchmark.md     # Test cases và kết quả so sánh
```

Không chép nguyên walkthrough từ tutorial. Tài liệu phải giải thích thứ tự mở rộng node, frontier/open list, cost/heuristic và cách tạo final route theo yêu cầu demo video.
